<template>
  <v-app>
    <v-navigation-drawer v-model="nav" :rail="rail && !mobile" rail-width="64" :permanent="!mobile" :temporary="mobile" color="transparent" width="260" class="app-nav" :border="0">
      <router-link to="/start" class="brand" style="text-decoration: none">
        <span class="icon-tile" aria-hidden="true"><v-icon>mdi-feather</v-icon></span>
        <span v-if="!rail">
          <span class="name d-block">Vogelring</span>
          <span class="sub d-block">Analyse</span>
        </span>
      </router-link>
      <v-list density="comfortable" nav aria-label="Hauptnavigation">
        <v-list-item v-for="it in items" :key="it.to" :to="it.to" :prepend-icon="it.icon" :title="it.title" :aria-label="rail ? it.title : undefined" />
      </v-list>
      <template #append>
        <div class="nav-foot">
          <v-list density="compact" nav>
            <v-list-item :href="meta.meta?.chat_url || 'https://chat.vogelring.com'" target="_blank" prepend-icon="mdi-chat-outline" title="Chat (neues Fenster)" />
            <v-list-item href="https://vogelring.com" target="_blank" prepend-icon="mdi-bird" title="vogelring.com" />
            <v-list-item v-if="rail" :prepend-icon="themeIcon" title="Darstellung" @click="cycleTheme" />
            <v-list-item :prepend-icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'" :title="rail ? 'Ausklappen' : 'Einklappen'" @click="rail = !rail" />
          </v-list>
          <div v-if="!rail" class="theme-switch" role="radiogroup" aria-label="Darstellung">
            <button v-for="t in THEMES" :key="t.value" type="button" role="radio" :aria-checked="themePref === t.value" :class="{ on: themePref === t.value }" :title="t.title" @click="setTheme(t.value)">
              <v-icon size="16">{{ t.icon }}</v-icon>
            </button>
          </div>
        </div>
      </template>
    </v-navigation-drawer>

    <v-app-bar flat color="transparent" height="56" class="app-bar" :border="0">
      <v-btn v-if="mobile" icon="mdi-menu" variant="text" aria-label="Menü" class="ml-1" @click="nav = !nav" />
      <v-app-bar-title>{{ title }}</v-app-bar-title>
      <button v-if="live.lastTitle && !mobile" type="button" class="live-chip mr-3" :class="{ off: !live.connected }" :title="live.connected ? 'Live verbunden' : 'Verbindung unterbrochen'" @click="router.push('/live')">
        <span class="dot" aria-hidden="true" /><span>{{ live.lastTitle }}</span>
      </button>
      <v-btn v-if="!mobile" color="primary" variant="flat" prepend-icon="mdi-robot-happy-outline" class="mr-1" @click="meta.openChat()">Agent fragen</v-btn>
      <v-btn v-else color="primary" variant="flat" icon="mdi-robot-happy-outline" aria-label="Agent fragen" class="mr-2" @click="meta.openChat()" />
    </v-app-bar>

    <v-main>
      <router-view v-slot="{ Component }">
        <keep-alive include="ErkundenPage">
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </v-main>

    <ChatDrawer />
    <v-snackbar v-model="meta.snackbar.show" :color="meta.snackbar.color" timeout="4000" location="bottom right">{{ meta.snackbar.text }}</v-snackbar>
  </v-app>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay, useTheme } from 'vuetify'
import ChatDrawer from '@/components/ChatDrawer.vue'
import { connectEvents } from '@/lib/events'
import { isDark, setTheme, themePref, type ThemePref } from '@/lib/theme'
import { useLiveStore } from '@/stores/live'
import { useMetaStore } from '@/stores/meta'

const meta = useMetaStore()
const live = useLiveStore()
const router = useRouter()
const route = useRoute()
const vTheme = useTheme()
const { mdAndDown: mobile } = useDisplay()
const nav = ref(!mobile.value)
const rail = ref(false)
const title = computed(() => (route.meta.title as string) || 'Vogelring Analyse')

const items = [
  { to: '/start', icon: 'mdi-home-outline', title: 'Start' },
  { to: '/live', icon: 'mdi-broadcast', title: 'Live' },
  { to: '/erkunden', icon: 'mdi-compass-outline', title: 'Daten erkunden' },
  { to: '/ansichten', icon: 'mdi-image-multiple-outline', title: 'Ansichten' },
  { to: '/gruppen', icon: 'mdi-folder-multiple-outline', title: 'Gruppen' },
  { to: '/mappen', icon: 'mdi-view-dashboard-outline', title: 'Mappen' },
  { to: '/auswertungen', icon: 'mdi-play-box-multiple-outline', title: 'Auswertungen' },
  { to: '/berichte', icon: 'mdi-file-document-multiple-outline', title: 'Berichte & Präsentationen' },
  { to: '/begriffe', icon: 'mdi-book-open-variant', title: 'Begriffe' },
  { to: '/notizen', icon: 'mdi-note-text-outline', title: 'Notizen' },
]

const THEMES: { value: ThemePref; icon: string; title: string }[] = [
  { value: 'light', icon: 'mdi-white-balance-sunny', title: 'Hell' },
  { value: 'dark', icon: 'mdi-weather-night', title: 'Dunkel' },
  { value: 'system', icon: 'mdi-monitor', title: 'Wie das System' },
]
const themeIcon = computed(() => THEMES.find((t) => t.value === themePref.value)?.icon || 'mdi-monitor')
function cycleTheme() {
  const i = THEMES.findIndex((t) => t.value === themePref.value)
  setTheme(THEMES[(i + 1) % THEMES.length].value)
}
watch(isDark, (d) => (vTheme.global.name.value = d ? 'dark' : 'light'), { immediate: true })
watch(mobile, (m) => (nav.value = !m))
watch(() => route.path, () => mobile.value && (nav.value = false))

onMounted(async () => {
  try {
    await meta.load()
  } catch (e) {
    meta.notify('Der Server antwortet nicht. Bitte Seite neu laden.', 'error')
  }
  connectEvents(router)
})
</script>
