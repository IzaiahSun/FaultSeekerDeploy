import asyncio
import io
import json
import os
import queue
import sys
import threading
import time
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

load_dotenv()

_DEFAULT_MODEL = os.getenv("FAULTSEEKER_MODEL", "openai/gpt-4o-mini")

app = FastAPI(title="FaultSeeker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Rate limiter (fixed 15-min window, max 10 requests) ──────────────────────
class _RateLimiter:
    def __init__(self, limit: int, window: int):
        self.limit = limit          # max requests per window
        self.window = window        # window length in seconds
        self._count = 0
        self._window_start = time.monotonic()
        self._lock = asyncio.Lock()

    def _maybe_reset(self):
        if time.monotonic() - self._window_start >= self.window:
            self._count = 0
            self._window_start = time.monotonic()

    async def check(self) -> None:
        """Increment counter; raise HTTP 429 if limit exceeded."""
        async with self._lock:
            self._maybe_reset()
            if self._count >= self.limit:
                secs = self.window - (time.monotonic() - self._window_start)
                mins, s = divmod(int(secs), 60)
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": f"Rate limit exceeded ({self.limit} requests / 15 min). "
                                   f"Resets in {mins}m {s:02d}s.",
                        **self._info(),
                    },
                )
            self._count += 1

    def _info(self) -> dict:
        self._maybe_reset()
        secs_left = max(0.0, self.window - (time.monotonic() - self._window_start))
        return {
            "count": self._count,
            "limit": self.limit,
            "remaining": max(0, self.limit - self._count),
            "reset_in_seconds": round(secs_left),
            "window_seconds": self.window,
        }

    async def status(self) -> dict:
        async with self._lock:
            return self._info()


_rl = _RateLimiter(limit=10, window=15 * 60)


SUPPORTED_CHAINS = {'bsc', 'eth', 'polygon', 'avalanche', 'arbitrum', 'base', 'pulsechain'}


class AnalyzeRequest(BaseModel):
    txn_link: Optional[str] = None
    txn_hash: Optional[str] = None
    chain: Optional[str] = None


class QueueStream(io.StringIO):
    """Captures writes (print output) and pushes them into a queue."""

    def __init__(self, q: queue.Queue):
        super().__init__()
        self._queue = q

    def write(self, text: str) -> int:
        if text and text != "\n":
            # Strip trailing newline so frontend can add its own
            self._queue.put(("log", text.rstrip("\n")))
        elif text == "\n":
            pass  # skip bare newlines
        return len(text)

    def flush(self):
        pass


def _run_pipeline(request: AnalyzeRequest, q: queue.Queue):
    """Runs the FaultSeeker pipeline in a background thread."""
    original_stdout = sys.stdout
    sys.stdout = QueueStream(q)
    try:
        from faultseeker.core.config import FaultSeekerConfig
        from faultseeker.core.pipeline import FaultSeekerPipeline

        config = FaultSeekerConfig(
            forensics_model=_DEFAULT_MODEL,
            function_analysis_model=_DEFAULT_MODEL,
            api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or None,
        )
        pipeline = FaultSeekerPipeline(config)

        result = pipeline.analyze_transaction(
            txn_link=request.txn_link,
            txn_hash=request.txn_hash,
            chain=request.chain,
        )
        print("Successfully completed analysis.")
        q.put(("result", result))
    except BaseException as exc:
        import traceback
        print(f"Failed with exception {exc}")
        q.put(("error", traceback.format_exc()))
    finally:
        print("Done")
        sys.stdout = original_stdout
        q.put(("done", None))


@app.get("/api/rate-limit")
async def rate_limit_status():
    return await _rl.status()


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    if request.chain and request.chain not in SUPPORTED_CHAINS:
        raise HTTPException(status_code=400, detail={"message": f"Chain '{request.chain}' is not supported. Supported chains: {', '.join(sorted(SUPPORTED_CHAINS))}"})
    await _rl.check()
    q: queue.Queue = queue.Queue()

    thread = threading.Thread(target=_run_pipeline, args=(request, q), daemon=True)
    thread.start()

    async def event_generator():
        loop = asyncio.get_running_loop()
        while True:
            try:
                kind, data = await loop.run_in_executor(None, lambda: q.get(timeout=600))
            except queue.Empty:
                yield {"event": "error", "data": json.dumps({"message": "Analysis timed out"})}
                break

            if kind == "done":
                break
            elif kind == "log":
                yield {"event": "log", "data": json.dumps({"message": data})}
            elif kind == "result":
                yield {"event": "result", "data": json.dumps(data, default=str)}
            elif kind == "error":
                yield {"event": "error", "data": json.dumps({"message": data})}
                break

    return EventSourceResponse(event_generator())
