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

// Register service worker for automatic updates
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then(registration => {
      console.log('ServiceWorker registration successful with scope: ', registration.scope);
      
      // Check for updates when the page loads
      if (registration.active) {
        registration.active.postMessage({ type: 'CHECK_UPDATE' });
      }
    }).catch(error => {
      console.log('ServiceWorker registration failed: ', error);
    });
    
    // Listen for messages from the service worker
    navigator.serviceWorker.addEventListener('message', event => {
      if (event.data && event.data.type === 'UPDATE_AVAILABLE') {
        console.log('New version available:', event.data.version);
        
        // Show a notification to the user
        const shouldUpdate = confirm(`A new version (${event.data.version}) is available. Reload now to update?`);
        
        if (shouldUpdate) {
          // Clear cache and reload the page
          window.location.reload();
        }
      }
    });
  });
}

const vuetify = createVuetify({
  components,
  directives,
  theme
})

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // Main application routes (no authentication required - handled by Cloudflare Zero Trust)
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
        },
        {
          path: 'seasonal',
          name: 'statistics-seasonal',
          component: () => import('./views/statistics/SeasonalAnalysisView.vue')
        },
        {
          path: 'data-quality',
          name: 'statistics-data-quality',
          component: () => import('./views/statistics/DataQualityView.vue')
        }
      ]
    },
    {
      path: '/birds/:ring',
      component: BirdDetail
    },
    {
      path: '/birds/:ring/environment-analysis',
      name: 'environment-analysis',
      component: () => import('./views/EnvironmentAnalysis.vue')
    },
    {
      path: '/ringing',
      name: 'ringing',
      component: () => import('./views/Ringing.vue')
    },
    // Legal pages
    {
      path: '/impressum',
      name: 'impressum',
      component: () => import('./views/legal/Impressum.vue')
    },
    {
      path: '/datenschutz',
      name: 'datenschutz',
      component: () => import('./views/legal/Datenschutz.vue')
    },
    {
      path: '/agb',
      name: 'agb',
      component: () => import('./views/legal/AGB.vue')
    },
    {
      path: '/widerruf',
      name: 'widerruf',
      component: () => import('./views/legal/Widerruf.vue')
    }
  ]
})

const pinia = createPinia()
const app = createApp(App)

app.use(vuetify)
app.use(pinia)
app.use(router)

app.mount('#app')