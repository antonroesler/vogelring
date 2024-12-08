import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import 'leaflet/dist/leaflet.css'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light'
  }
})

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/new-entry'
    },
    {
      path: '/new-entry',
      component: () => import('./views/NewEntry.vue')
    },
    {
      path: '/entries',
      component: () => import('./views/EntryList.vue')
    },
    {
      path: '/entry/:id',
      component: () => import('./views/EntryDetail.vue')
    },
    {
      path: '/statistics',
      component: () => import('./views/Statistics.vue')
    }
  ]
})

const pinia = createPinia()
const app = createApp(App)

app.use(vuetify)
app.use(router)
app.use(pinia)
app.mount('#app')