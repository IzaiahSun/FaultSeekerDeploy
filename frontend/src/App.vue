<template>
  <div class="app">
    <header class="header">
      <h1>FaultSeeker <span class="subtitle">Smart Contract Vulnerability Analyzer</span></h1>
    </header>

    <main class="main">
      <AnalysisForm ref="formRef" :running="running" @submit="startAnalysis" />
      <LogStream :logs="logs" />
      <ResultView :result="result" :error="analysisError" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AnalysisForm from './components/AnalysisForm.vue'
import LogStream from './components/LogStream.vue'
import ResultView from './components/ResultView.vue'

const running = ref(false)
const logs = ref([])
const result = ref(null)
const analysisError = ref(null)
const formRef = ref(null)

// Call backend directly to avoid Vite proxy buffering SSE streams.
// CORS is enabled on the backend so cross-origin fetch works fine.
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

async function startAnalysis(form) {
  running.value = true
  logs.value = []
  result.value = null
  analysisError.value = null

  const payload = {
    txn_link: form.txn_link || null,
    txn_hash: form.txn_hash || null,
    chain: form.chain || null,
  }

  try {
    const response = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    // Handle rate limit (429) before trying to read as SSE
    if (response.status === 429) {
      const data = await response.json()
      analysisError.value = data.detail?.message ?? 'Rate limit exceeded.'
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // SSE messages separated by \r\n\r\n (sse-starlette) or \n\n
      const parts = buffer.split(/\r\n\r\n|\n\n/)
      buffer = parts.pop() // keep incomplete tail

      for (const part of parts) {
        let eventType = 'message'
        let dataLine = ''
        for (const line of part.split(/\r\n|\n/)) {
          if (line.startsWith('event:')) eventType = line.slice(6).trim()
          else if (line.startsWith('data:')) dataLine = line.slice(5).trim()
        }
        if (!dataLine) continue
        const parsed = JSON.parse(dataLine)

        if (eventType === 'log') {
          logs.value.push(parsed.message)
        } else if (eventType === 'result') {
          result.value = parsed
        } else if (eventType === 'error') {
          analysisError.value = parsed.message
        }
      }
    }
  } catch (err) {
    analysisError.value = String(err)
  } finally {
    running.value = false
    formRef.value?.fetchRl()
  }
}
</script>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', system-ui, sans-serif;
  background: #f1f5f9;
  color: #1e293b;
  min-height: 100vh;
}

.app { display: flex; flex-direction: column; min-height: 100vh; }

.header {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 1rem 2rem;
}
.header h1 { font-size: 1.4rem; font-weight: 700; color: #7c3aed; }
.subtitle { font-size: 0.85rem; font-weight: 400; color: #94a3b8; margin-left: 0.5rem; }

.main { max-width: 900px; margin: 0 auto; padding: 2rem 1rem; display: flex; flex-direction: column; gap: 1.5rem; width: 100%; }

.form-card, .log-card, .result-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
}

.section-title { font-size: 1rem; font-weight: 600; color: #7c3aed; margin-bottom: 1rem; }
.subsection-title { font-size: 0.9rem; font-weight: 600; color: #64748b; margin-bottom: 0.5rem; }

.field { display: flex; flex-direction: column; gap: 0.4rem; flex: 1; }
.field label { font-size: 0.8rem; color: #64748b; }
.field input, .field select {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #1e293b;
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
}
.field input:focus, .field select:focus { border-color: #7c3aed; }
.row { display: flex; gap: 1rem; }

.btn-primary {
  margin-top: 0.5rem;
  background: #7c3aed;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.6rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-primary:hover:not(:disabled) { background: #6d28d9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.log-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
  max-height: 320px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  line-height: 1.6;
}
.log-line { color: #475569; white-space: pre-wrap; word-break: break-all; }

.error-box {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 1rem;
  color: #dc2626;
  font-size: 0.82rem;
}
.result-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.result-table th { text-align: left; padding: 0.4rem 0.6rem; color: #94a3b8; border-bottom: 1px solid #e2e8f0; }
.result-table td { padding: 0.4rem 0.6rem; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
.mono { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }
.vuln-box, .raw-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
  font-size: 0.78rem;
  white-space: pre-wrap;
  word-break: break-all;
  color: #475569;
  max-height: 400px;
  overflow-y: auto;
}
.mt-4 { margin-top: 1rem; }
</style>
