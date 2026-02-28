<template>
  <div v-if="result || error">

    <!-- ── Error ── -->
    <div v-if="error" class="result-card">
      <div class="section-header">
        <span class="status-dot dot-error"></span>
        <h2 class="section-title">Analysis Failed</h2>
      </div>
      <pre class="error-box">{{ error }}</pre>
    </div>

    <!-- ── Result ── -->
    <div v-else-if="result" class="result-root">

      <!-- 1. Transaction Meta Bar -->
      <div class="meta-bar">
        <div class="meta-left">
          <span class="status-dot dot-ok"></span>
          <span class="chain-badge">{{ result.chain?.toUpperCase() ?? 'CHAIN' }}</span>
          <span class="txn-hash mono" :title="result.transaction_hash">
            {{ shortHash(result.transaction_hash) }}
          </span>
          <button class="copy-btn" @click="copy(result.transaction_hash)" title="Copy hash">⎘</button>
        </div>
        <div class="meta-right">
          <span class="meta-chip">🕒 {{ formatTs(result.timestamp) }}</span>
          <span class="meta-chip">⏱ {{ formatDur(result.duration) }}</span>
          <span v-if="result._debug" class="meta-chip">🔍 {{ result._debug.functions_to_inspect_count }} fn inspected</span>
        </div>
      </div>

      <!-- 2. Potential Vulnerabilities (prominent, top) -->
      <div class="vuln-card" v-if="vulnEntries.length">
        <div class="vuln-card-header">
          <div class="vuln-card-title-row">
            <span class="vuln-fire">🔥</span>
            <h3 class="vuln-card-title">Potential Vulnerabilities</h3>
            <span class="vuln-count-badge">{{ vulnEntries.length }} function{{ vulnEntries.length > 1 ? 's' : '' }}</span>
          </div>
          <p class="vuln-card-sub">The following functions were identified as potentially exploitable.</p>
        </div>
        <div class="vuln-list">
          <div v-for="([fn, reasons], idx) in vulnEntries" :key="fn" class="vuln-item">
            <button class="vuln-header" @click="toggle(fn)">
              <div class="vuln-fn-name">
                <span class="vuln-idx">{{ idx + 1 }}</span>
                <div class="vuln-fn-text">
                  <span class="vuln-fn-label mono">{{ parseFn(fn).name }}</span>
                  <span v-if="parseFn(fn).addr" class="vuln-addr mono">{{ parseFn(fn).addr }}</span>
                </div>
              </div>
              <div class="vuln-header-right">
                <span class="reason-count">{{ reasons.length }} finding{{ reasons.length > 1 ? 's' : '' }}</span>
                <span class="chevron">{{ expanded[fn] ? '▲' : '▼' }}</span>
              </div>
            </button>
            <div v-show="expanded[fn]" class="vuln-reasons">
              <div v-for="(r, j) in reasons" :key="j" class="reason-item">
                <span class="reason-num">{{ j + 1 }}</span>
                <span>{{ r }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. Ranked Suspicious Functions -->
      <div class="result-card" v-if="ranked.length">
        <h3 class="card-title">Ranked Suspicious Functions</h3>
        <div class="fn-list">
          <div v-for="(fn, i) in ranked" :key="fn" class="fn-row">
            <div class="rank-badge" :class="`rank-${Math.min(i+1, 4)}`">{{ i + 1 }}</div>
            <div class="fn-body">
              <div class="fn-name mono">{{ parseFn(fn).name }}</div>
              <div v-if="parseFn(fn).addr" class="fn-addr mono">
                {{ parseFn(fn).addr }}
              </div>
            </div>
            <div v-if="vulnDetails[fn]" class="vuln-tag">⚠ Vulnerable</div>
          </div>
        </div>
      </div>

      <!-- 4. Transaction Understanding -->
      <div class="result-card" v-if="result.transaction_understanding">
        <h3 class="card-title">Transaction Analysis</h3>
        <div class="md-body" v-html="renderMd(result.transaction_understanding)"></div>
      </div>

      <!-- 5. Debug / Timing -->
      <details class="debug-card" v-if="result._debug">
        <summary>Debug · Timing</summary>
        <div class="debug-grid">
          <div class="debug-item">
            <div class="debug-label">Forensics</div>
            <div class="debug-val">{{ formatDur(result._debug.forensics_duration) }}</div>
          </div>
          <div class="debug-item">
            <div class="debug-label">Analysis</div>
            <div class="debug-val">{{ formatDur(result._debug.analysis_duration) }}</div>
          </div>
          <div class="debug-item">
            <div class="debug-label">Functions inspected</div>
            <div class="debug-val">{{ result._debug.functions_to_inspect_count }}</div>
          </div>
        </div>
      </details>

    </div>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'

const props = defineProps({ result: Object, error: String })

// ── data helpers ──────────────────────────────────────────────
const ranked = computed(() => props.result?.ranked_suspicious_functions ?? [])
const vulnDetails = computed(() => props.result?.potentially_vulnerable_functions ?? {})
const vulnEntries = computed(() => Object.entries(vulnDetails.value))

// ── expanded state for accordion ─────────────────────────────
const expanded = reactive({})
function toggle(fn) { expanded[fn] = !expanded[fn] }

// ── formatters ────────────────────────────────────────────────
function shortHash(h) {
  if (!h) return '—'
  return h.slice(0, 10) + '…' + h.slice(-8)
}

function copy(text) {
  if (text) navigator.clipboard.writeText(text).catch(() => {})
}

function formatTs(ts) {
  if (!ts) return '—'
  try { return new Date(ts).toLocaleString() } catch { return ts }
}

function formatDur(s) {
  if (s == null) return '—'
  if (s < 60) return `${s.toFixed(1)}s`
  const m = Math.floor(s / 60), sec = (s % 60).toFixed(0)
  return `${m}m ${sec}s`
}

// fn_name_0xADDRESS → { name, addr }
function parseFn(fn) {
  const m = fn.match(/^(.*?)_(0x[0-9a-fA-F]{40})$/)
  if (m) return { name: m[1], addr: m[2] }
  return { name: fn, addr: null }
}

// ── minimal markdown → HTML ───────────────────────────────────
function renderMd(raw) {
  if (!raw) return ''
  let s = raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // inline code
    .replace(/`([^`\n]+)`/g, '<code class="ic">$1</code>')
    // headings (## or ###)
    .replace(/^#{3} (.+)$/gm, '<h5 class="md-h">$1</h5>')
    .replace(/^#{2} (.+)$/gm, '<h4 class="md-h">$1</h4>')
    // list items
    .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
  // wrap consecutive <li> in <ul>
  s = s.replace(/(<li>.*?<\/li>\n?)+/gs, m => `<ul class="md-ul">${m}</ul>`)
  // paragraphs
  s = s.replace(/\n\n+/g, '</p><p class="md-p">').replace(/\n/g, '<br>')
  return `<p class="md-p">${s}</p>`
}
</script>

<style scoped>
/* ── Root ── */
.result-root { display: flex; flex-direction: column; gap: 1rem; }

/* ── Meta bar ── */
.meta-bar {
  display: flex; justify-content: space-between; align-items: center;
  background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 0.75rem 1.25rem; gap: 1rem; flex-wrap: wrap;
}
.meta-left { display: flex; align-items: center; gap: 0.6rem; }
.meta-right { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }

.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-ok { background: #22c55e; box-shadow: 0 0 6px #22c55e88; }
.dot-error { background: #ef4444; box-shadow: 0 0 6px #ef444488; }

.chain-badge {
  background: #f5f3ff; color: #7c3aed;
  border: 1px solid #ddd6fe; border-radius: 6px;
  padding: 0.2rem 0.55rem; font-size: 0.75rem; font-weight: 700; letter-spacing: .05em;
}
.txn-hash { color: #64748b; font-size: 0.82rem; }
.copy-btn {
  background: none; border: none; color: #94a3b8; cursor: pointer;
  font-size: 1rem; padding: 0 0.2rem; line-height: 1;
  transition: color .15s;
}
.copy-btn:hover { color: #7c3aed; }
.meta-chip { font-size: 0.78rem; color: #94a3b8; }

/* ── Cards ── */
.result-card {
  background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 1.25rem 1.5rem;
}
.card-title {
  font-size: 0.85rem; font-weight: 700; color: #7c3aed;
  text-transform: uppercase; letter-spacing: .07em; margin-bottom: 1rem;
}

/* ── Error ── */
.section-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.75rem; }
.section-title { font-size: 1rem; font-weight: 600; color: #dc2626; }
.error-box {
  background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;
  padding: 1rem; color: #dc2626; font-size: 0.78rem;
  white-space: pre-wrap; word-break: break-all; max-height: 400px; overflow-y: auto;
}

/* ── Ranked Functions ── */
.fn-list { display: flex; flex-direction: column; gap: 0.6rem; }
.fn-row {
  display: flex; align-items: flex-start; gap: 0.75rem;
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 0.7rem 0.9rem;
  transition: border-color .15s;
}
.fn-row:hover { border-color: #c4b5fd; }

.rank-badge {
  min-width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.8rem; font-weight: 800; flex-shrink: 0; margin-top: 1px;
}
.rank-1 { background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }
.rank-2 { background: #fff7ed; color: #ea580c; border: 1px solid #fdba74; }
.rank-3 { background: #fefce8; color: #ca8a04; border: 1px solid #fde047; }
.rank-4 { background: #f8fafc; color: #64748b; border: 1px solid #cbd5e1; }

.fn-body { flex: 1; min-width: 0; }
.fn-name { color: #1e293b; font-size: 0.88rem; word-break: break-all; }
.fn-addr { color: #94a3b8; font-size: 0.75rem; margin-top: 0.15rem; word-break: break-all; }

.vuln-tag {
  flex-shrink: 0; background: #fff7ed; color: #ea580c;
  border: 1px solid #fed7aa; border-radius: 5px;
  font-size: 0.7rem; font-weight: 600; padding: 0.2rem 0.5rem;
  align-self: flex-start;
}

/* ── Prominent Vulnerability Card ── */
.vuln-card {
  background: linear-gradient(135deg, #fdf4ff 0%, #ffffff 60%);
  border: 1px solid #e9d5ff;
  border-left: 3px solid #ef4444;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 0 24px #ef444408;
}
.vuln-card-header {
  padding: 1.1rem 1.5rem 0.9rem;
  border-bottom: 1px solid #f3e8ff;
  background: #faf5ff;
}
.vuln-card-title-row { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.3rem; }
.vuln-fire { font-size: 1.1rem; }
.vuln-card-title {
  font-size: 1rem; font-weight: 700; color: #dc2626;
  text-transform: uppercase; letter-spacing: .06em;
}
.vuln-count-badge {
  background: #fef2f2; color: #dc2626;
  border: 1px solid #fca5a5; border-radius: 99px;
  font-size: 0.7rem; font-weight: 700; padding: 0.15rem 0.6rem;
}
.vuln-card-sub { font-size: 0.78rem; color: #9f7aea; margin: 0; }

/* ── Accordion (shared between vuln-card and any future use) ── */
.vuln-list { display: flex; flex-direction: column; gap: 0; }
.vuln-item { border-bottom: 1px solid #f3e8ff; }
.vuln-item:last-child { border-bottom: none; }

.vuln-header {
  display: flex; justify-content: space-between; align-items: center;
  width: 100%; background: transparent; border: none; cursor: pointer;
  padding: 0.9rem 1.5rem; color: #1e293b; text-align: left;
  transition: background .15s;
}
.vuln-header:hover { background: #f5f3ff; }

.vuln-fn-name { display: flex; align-items: center; gap: 0.65rem; min-width: 0; flex: 1; }
.vuln-idx {
  min-width: 22px; height: 22px; border-radius: 50%;
  background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5;
  font-size: 0.72rem; font-weight: 800;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.vuln-fn-text { display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; }
.vuln-fn-label { color: #dc2626; font-size: 0.88rem; font-weight: 600; word-break: break-all; }
.vuln-addr { color: #c4b5fd; font-size: 0.72rem; word-break: break-all; }

.vuln-header-right { display: flex; align-items: center; gap: 0.6rem; flex-shrink: 0; }
.reason-count { font-size: 0.72rem; color: #7c3aed; }
.chevron { color: #7c3aed; font-size: 0.68rem; }

.vuln-reasons {
  background: #faf5ff; padding: 0.75rem 1.5rem 0.9rem 1.5rem;
  border-top: 1px solid #f3e8ff;
  display: flex; flex-direction: column; gap: 0.55rem;
}
.reason-item { display: flex; gap: 0.65rem; color: #4b5563; font-size: 0.83rem; line-height: 1.6; align-items: flex-start; }
.reason-num {
  min-width: 18px; height: 18px; border-radius: 4px;
  background: #f5f3ff; color: #7c3aed;
  font-size: 0.68rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 2px;
}

/* ── Markdown body ── */
.md-body { color: #475569; font-size: 0.85rem; line-height: 1.7; }
:deep(.md-p) { margin: 0 0 0.75rem; }
:deep(.md-p:last-child) { margin-bottom: 0; }
:deep(.md-h) { color: #334155; font-size: 0.85rem; font-weight: 700; margin: 0.9rem 0 0.3rem; }
:deep(.md-ul) { padding-left: 1.2rem; margin: 0.3rem 0; }
:deep(.md-ul li) { margin-bottom: 0.25rem; }
:deep(.ic) {
  font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;
  background: #f5f3ff; color: #7c3aed; border-radius: 4px;
  padding: 0.1em 0.35em;
}
:deep(strong) { color: #1e293b; font-weight: 600; }

/* ── Debug card ── */
.debug-card {
  background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 0.75rem 1.25rem; color: #94a3b8; font-size: 0.8rem;
}
.debug-card summary { cursor: pointer; user-select: none; }
.debug-grid {
  display: flex; gap: 1.5rem; flex-wrap: wrap;
  margin-top: 0.75rem; padding-top: 0.75rem;
  border-top: 1px solid #f1f5f9;
}
.debug-item { display: flex; flex-direction: column; gap: 0.2rem; }
.debug-label { color: #94a3b8; font-size: 0.72rem; text-transform: uppercase; letter-spacing: .05em; }
.debug-val { color: #64748b; font-size: 0.85rem; font-weight: 600; }

/* ── shared ── */
.mono { font-family: 'JetBrains Mono', monospace; }
</style>
