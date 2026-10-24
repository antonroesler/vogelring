import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import { de } from 'vuetify/locale'

// Theme colours mirror the CSS tokens in styles.css (see DESIGN.md). `secondary` maps to the brand colour too:
// the only accent is the Vogelring blue; status colours follow LibreChat.
const light = {
  dark: false,
  colors: {
    primary: '#00436C',
    secondary: '#00436C',
    accent: '#00436C',
    error: '#B91C1C',
    info: '#00436C',
    success: '#047857',
    warning: '#B45309',
    background: '#FFFFFF',
    surface: '#FFFFFF',
    'surface-bright': '#FFFFFF',
    'surface-light': '#F7F7F8',
    'surface-variant': '#ECECEC',
    'on-surface-variant': '#212121',
    'on-surface': '#212121',
    'on-background': '#212121',
    'on-primary': '#FFFFFF',
    'on-secondary': '#FFFFFF',
  },
}

const dark = {
  dark: true,
  colors: {
    primary: '#7DB9E6',
    secondary: '#7DB9E6',
    accent: '#7DB9E6',
    error: '#F87171',
    info: '#7DB9E6',
    success: '#10B981',
    warning: '#FBBF24',
    background: '#0D0D0D',
    surface: '#0D0D0D',
    'surface-bright': '#171717',
    'surface-light': '#212121',
    'surface-variant': '#2F2F2F',
    'on-surface-variant': '#ECECEC',
    'on-surface': '#ECECEC',
    'on-background': '#ECECEC',
    'on-primary': '#0D0D0D',
    'on-secondary': '#0D0D0D',
  },
}

export const vuetify = createVuetify({
  locale: { locale: 'de', messages: { de } },
  theme: { defaultTheme: 'light', themes: { light, dark } },
  defaults: {
    VBtn: { rounded: 'pill', variant: 'flat' },
    VCard: { rounded: 'lg', elevation: 0, variant: 'flat' },
    VTextField: { variant: 'outlined', density: 'comfortable', color: 'primary' },
    VSelect: { variant: 'outlined', density: 'comfortable', color: 'primary' },
    VAutocomplete: { variant: 'outlined', density: 'comfortable', color: 'primary' },
    VCombobox: { variant: 'outlined', density: 'comfortable', color: 'primary' },
    VTextarea: { variant: 'outlined', color: 'primary' },
    VCheckbox: { color: 'primary', density: 'comfortable' },
    VSwitch: { color: 'primary', inset: true, density: 'comfortable' },
    VBtnToggle: { divided: true, variant: 'outlined', color: 'primary', density: 'comfortable' },
    VList: { density: 'comfortable' },
    VChip: { variant: 'tonal', size: 'small' },
    VAlert: { variant: 'tonal', density: 'comfortable' },
    VTooltip: { location: 'top' },
    VDialog: { scrim: 'black' },
    VProgressLinear: { color: 'primary', rounded: true },
    VProgressCircular: { color: 'primary' },
  },
})
