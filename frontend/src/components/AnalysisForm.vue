<template>
  <form @submit.prevent="$emit('submit', form)" class="form-card">
    <div class="form-top">
      <h2 class="section-title">Transaction Analysis</h2>
      <!-- Rate limit indicator -->
      <div class="rl-pill" :class="rlClass" :title="rlTitle">
        <span class="rl-dot"></span>
        <span class="rl-text">{{ rlLabel }}</span>
      </div>
    </div>

    <div class="field">
      <label>Transaction Link</label>
      <input v-model="form.txn_link" type="text" placeholder="https://bscscan.com/tx/0x..." />
    </div>

    <div class="row">
      <div class="field">
        <label>Transaction Hash</label>
        <input v-model="form.txn_hash" type="text" placeholder="0x..." />
      </div>
      <div class="field">
        <label>Chain</label>
        <select v-model="form.chain">
          <option value="">Auto-detect</option>
          <option v-for="c in chains" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
    </div>

    <div class="form-bottom">
      <button type="submit" :disabled="running || rl.remaining === 0" class="btn-primary">
        {{ running ? 'Analyzing…' : 'Analyze' }}
      </button>
      <!-- Progress bar -->
      <div class="rl-bar-wrap" v-if="rl.limit">
        <div class="rl-bar-track">
          <div class="rl-bar-fill" :class="rlClass" :style="{ width: rlPct + '%' }"></div>
        </div>
        <span class="rl-bar-label">{{ rl.count }}&thinsp;/&thinsp;{{ rl.limit }} &nbsp;·&nbsp; resets in {{ resetLabel }}</span>
      </div>
    </div>
  </form>
</template>

<script setup>
import { reactive, ref, computed, onMounted, onUnmounted } from 'vue'

defineProps({ running: Boolean })
defineEmits(['submit'])

const chains = ['bsc', 'eth', 'polygon', 'avalanche', 'arbitrum', 'base', 'pulsechain']

const form = reactive({ txn_link: '', txn_hash: '', chain: '' })

// ── rate limit state ──────────────────────────────────────────
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

const rl = ref({ count: 0, limit: 10, remaining: 10, reset_in_seconds: 900, window_seconds: 900 })

async function fetchRl() {
  try {
    const r = await fetch(`${API_BASE}/api/rate-limit`)
    if (r.ok) rl.value = await r.json()
  } catch {}
}

// expose so parent can refresh after a request
defineExpose({ fetchRl })

let timer = null
onMounted(() => { fetchRl(); timer = setInterval(fetchRl, 15_000) })
onUnmounted(() => clearInterval(timer))

// ── computed display ──────────────────────────────────────────
const rlPct = computed(() => rl.value.limit ? (rl.value.count / rl.value.limit) * 100 : 0)

const rlClass = computed(() => {
  const pct = rlPct.value
  if (pct >= 100) return 'rl-full'
  if (pct >= 70)  return 'rl-warn'
  return 'rl-ok'
})

const rlLabel = computed(() => {
  if (rl.value.remaining === 0) return 'Limit reached'
  return `${rl.value.remaining} left`
})

const rlTitle = computed(() =>
  `${rl.value.count} / ${rl.value.limit} requests used · resets in ${resetLabel.value}`
)

const resetLabel = computed(() => {
  const s = rl.value.reset_in_seconds ?? 0
  if (s <= 0) return '0s'
  const m = Math.floor(s / 60), sec = s % 60
  return m > 0 ? `${m}m ${sec.toString().padStart(2, '0')}s` : `${sec}s`
})
</script>

<style scoped>
.form-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }

/* pill */
.rl-pill {
  display: flex; align-items: center; gap: 0.35rem;
  border-radius: 99px; padding: 0.2rem 0.65rem;
  font-size: 0.72rem; font-weight: 600; border: 1px solid;
  transition: all .2s;
}
.rl-ok   { background: #f0fdf4; color: #16a34a; border-color: #bbf7d0; }
.rl-warn { background: #fffbeb; color: #d97706; border-color: #fde68a; }
.rl-full { background: #fef2f2; color: #dc2626; border-color: #fecaca; }

.rl-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

/* bottom row */
.form-bottom { display: flex; align-items: center; gap: 1.25rem; flex-wrap: wrap; margin-top: 0.5rem; }

/* bar */
.rl-bar-wrap { display: flex; align-items: center; gap: 0.5rem; flex: 1; min-width: 160px; }
.rl-bar-track {
  flex: 1; height: 4px; background: #e2e8f0; border-radius: 99px; overflow: hidden;
}
.rl-bar-fill  { height: 100%; border-radius: 99px; transition: width .4s, background .3s; }
.rl-ok   .rl-bar-fill, .rl-bar-fill.rl-ok   { background: #4ade80; }
.rl-warn .rl-bar-fill, .rl-bar-fill.rl-warn { background: #fbbf24; }
.rl-full .rl-bar-fill, .rl-bar-fill.rl-full { background: #f87171; }
.rl-bar-label { font-size: 0.72rem; color: #94a3b8; white-space: nowrap; }
</style>
