<template>
  <v-navigation-drawer v-model="meta.chatOpen" location="right" :width="mobile ? display.width.value : width" :temporary="mobile" :scrim="mobile" class="chat-drawer">
    <div class="chat-head">
      <span class="icon-tile" aria-hidden="true"><v-icon>mdi-robot-happy-outline</v-icon></span>
      <span>Vogelring-Assistent</span>
      <v-spacer />
      <v-btn icon="mdi-open-in-new" size="small" variant="text" :href="url" target="_blank" title="Im Chat öffnen" />
      <v-btn icon="mdi-arrow-expand-horizontal" size="small" variant="text" title="Breiter / schmaler" @click="width = width > 520 ? 480 : 760" />
      <v-btn icon="mdi-close" size="small" variant="text" @click="meta.chatOpen = false" />
    </div>
    <iframe v-if="src" :key="frameKey" :src="src" class="chat-frame" allow="clipboard-write; microphone" />
    <div v-else class="pa-4 muted">Chat wird geladen …</div>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useDisplay } from 'vuetify'
import { useMetaStore } from '@/stores/meta'

const meta = useMetaStore()
const display = useDisplay()
const mobile = display.mdAndDown
const width = ref(480)
const frameKey = ref(0)
const src = ref('')

const url = computed(() => (meta.chatPrompt ? `${meta.chatBase}&prompt=${encodeURIComponent(meta.chatPrompt)}&submit=true` : meta.chatBase))

// Load the iframe once; only reload when a new prompt is handed over (chatNonce bumps).
watch(
  () => [meta.chatBase, meta.chatNonce] as const,
  ([base, nonce]) => {
    if (!base) return
    if (!src.value || (nonce && meta.chatPrompt)) {
      src.value = url.value
      frameKey.value++
    }
  },
  { immediate: true },
)
</script>

<style scoped>
.chat-drawer { z-index: 1500; }
</style>
