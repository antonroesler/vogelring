<template>
  <v-card class="empty-state pa-8 text-center">
    <v-icon size="40" class="mb-3 muted">{{ icon }}</v-icon>
    <div v-if="title" class="card-title mb-1">{{ title }}</div>
    <div class="text-small" style="max-width: 560px; margin: 0 auto; color: rgb(var(--text-secondary))">{{ text }}</div>
    <div v-if="$slots.default" class="mt-4 d-flex justify-center ga-2 flex-wrap"><slot /></div>
  </v-card>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ text: string; icon?: string; title?: string }>(), { icon: 'mdi-information-outline', title: '' })
</script>
