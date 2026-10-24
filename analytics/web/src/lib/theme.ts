/** Light / dark / system theme preference, shared by Vuetify, the CSS tokens (html.dark) and the chart/map renderers. */
import { computed, ref, watch } from 'vue'

export type ThemePref = 'light' | 'dark' | 'system'
const KEY = 'vr-theme'
const hasWindow = typeof window !== 'undefined'

function load(): ThemePref {
  try {
    const v = hasWindow ? localStorage.getItem(KEY) : null
    return v === 'light' || v === 'dark' ? v : 'system'
  } catch {
    return 'system'
  }
}

const mq = hasWindow && window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null
export const themePref = ref<ThemePref>(load())
const systemDark = ref(!!mq?.matches)
mq?.addEventListener?.('change', (e) => (systemDark.value = e.matches))

export const isDark = computed(() => themePref.value === 'dark' || (themePref.value === 'system' && systemDark.value))

export function setTheme(p: ThemePref) {
  themePref.value = p
  try {
    if (p === 'system') localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, p)
  } catch {
    /* private mode etc. */
  }
}

/** Applies the html.dark class as early as possible (before Vuetify mounts) and keeps it in sync. */
export function installThemeClass() {
  if (!hasWindow) return
  const apply = () => document.documentElement.classList.toggle('dark', isDark.value)
  apply()
  watch(isDark, apply)
}

/** Read a design token (RGB triple) as a CSS colour string; falls back when no DOM (tests). */
export function token(name: string, fallback: string, alpha?: number): string {
  if (!hasWindow) return fallback
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  if (!v) return fallback
  return alpha === undefined ? `rgb(${v})` : `rgba(${v.split(/\s+/).join(',')},${alpha})`
}
