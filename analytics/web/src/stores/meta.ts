import { defineStore } from 'pinia'
import { api, type Definition, type Meta, type SourcesInfo } from '@/api/client'

export const useMetaStore = defineStore('meta', {
  state: () => ({
    meta: null as Meta | null,
    sources: null as SourcesInfo | null,
    definitions: [] as Definition[],
    chatOpen: false,
    chatPrompt: '' as string,
    chatNonce: 0,
    snackbar: { show: false, text: '', color: 'primary' } as { show: boolean; text: string; color: string },
  }),
  getters: {
    chatBase: (s) => (s.meta ? `${s.meta.chat_url}/c/new?agent_id=${encodeURIComponent(s.meta.chat_agent_id)}` : ''),
    sourceByKey: (s) => (key: string) => s.sources?.sources.find((x) => x.key === key),
    dimensionLabel: (s) => (key: string | null | undefined) => s.sources?.dimensions.find((d) => d.key === key)?.label || key || '',
    metricLabel: (s) => (key: string) => s.sources?.metrics.find((m) => m.key === key)?.label || key,
    definitionsOf: (s) => (kind: string) => s.definitions.filter((d) => d.kind === kind),
  },
  actions: {
    async load() {
      const [meta, sources, defs] = await Promise.all([api.meta(), api.sources(), api.definitions()])
      this.meta = meta
      this.sources = sources
      this.definitions = defs.items
    },
    async reloadDefinitions() {
      this.definitions = (await api.definitions()).items
    },
    openChat(prompt?: string) {
      this.chatPrompt = prompt || ''
      this.chatNonce++
      this.chatOpen = true
    },
    notify(text: string, color = 'primary') {
      this.snackbar = { show: true, text, color }
    },
  },
})
