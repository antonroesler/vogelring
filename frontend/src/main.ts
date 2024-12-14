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
import { theme } from './theme'
import BirdDetail from './views/BirdDetail.vue'

const vuetify = createVuetify({
  components,
  directives,
  theme
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
      path: '/entries/:id',
      component: () => import('./views/EntryDetail.vue')
    },
    {
      path: '/statistics',
      component: () => import('./views/Statistics.vue'),
      children: [
        {
          path: '',
          redirect: { name: 'statistics-dashboard' }
        },
        {
          path: 'dashboard',
          name: 'statistics-dashboard',
          component: () => import('./views/statistics/DashboardView.vue')
        },
        {
          path: 'friends',
          name: 'statistics-friends',
          component: () => import('./views/statistics/FriendsView.vue')
        },
        {
          path: 'radius',
          name: 'statistics-radius',
          component: () => import('./views/statistics/RadiusView.vue')
        }
      ]
    },
    {
      path: '/birds/:ring',
      component: BirdDetail
    }
  ]
})

const pinia = createPinia()
const app = createApp(App)

app.use(vuetify)
app.use(router)
app.use(pinia)
app.mount('#app')