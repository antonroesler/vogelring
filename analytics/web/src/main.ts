import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { router } from './router'
import { vuetify } from './plugins/vuetify'
import { installThemeClass } from './lib/theme'
import '@fontsource-variable/inter'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import './styles.css'

installThemeClass()
createApp(App).use(createPinia()).use(router).use(vuetify).mount('#app')
