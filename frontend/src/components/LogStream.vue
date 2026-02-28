<template>
  <div class="log-card" v-if="logs.length">
    <h2 class="section-title">Analysis Log</h2>
    <div class="log-box" ref="box">
      <div v-for="(line, i) in logs" :key="i" class="log-line">{{ line }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({ logs: Array })
const box = ref(null)

watch(
  () => props.logs.length,
  async () => {
    await nextTick()
    if (box.value) box.value.scrollTop = box.value.scrollHeight
  }
)
</script>
