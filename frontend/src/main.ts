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
import { useAuthStore } from './stores/auth'

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
    // Authentication routes (public)
    {
      path: '/auth/login',
      name: 'login',
      component: () => import('./views/auth/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/auth/register',
      name: 'register',
      component: () => import('./views/auth/Register.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/auth/confirm',
      name: 'confirm-signup',
      component: () => import('./views/auth/ConfirmSignUp.vue'),
      meta: { requiresAuth: false }
    },
    // Protected routes (require authentication)
    {
      path: '/',
      redirect: '/new-entry',
      meta: { requiresAuth: true }
    },
    {
      path: '/new-entry',
      component: () => import('./views/NewEntry.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/entries',
      component: () => import('./views/EntryList.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/entries/:id',
      component: () => import('./views/EntryDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/statistics',
      component: () => import('./views/Statistics.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: { name: 'statistics-dashboard' }
        },
        {
          path: 'dashboard',
          name: 'statistics-dashboard',
          component: () => import('./views/statistics/DashboardView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'friends',
          name: 'statistics-friends',
          component: () => import('./views/statistics/FriendsView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'radius',
          name: 'statistics-radius',
          component: () => import('./views/statistics/RadiusView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'seasonal',
          name: 'statistics-seasonal',
          component: () => import('./views/statistics/SeasonalAnalysisView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'data-quality',
          name: 'statistics-data-quality',
          component: () => import('./views/statistics/DataQualityView.vue'),
          meta: { requiresAuth: true }
        }
      ]
    },
    {
      path: '/birds/:ring',
      component: BirdDetail,
      meta: { requiresAuth: true }
    },
    {
      path: '/birds/:ring/environment-analysis',
      name: 'environment-analysis',
      component: () => import('./views/EnvironmentAnalysis.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/ringing',
      name: 'ringing',
      component: () => import('./views/Ringing.vue'),
      meta: { requiresAuth: true }
    },
    // Legal pages (public)
    {
      path: '/impressum',
      name: 'impressum',
      component: () => import('./views/legal/Impressum.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/datenschutz',
      name: 'datenschutz',
      component: () => import('./views/legal/Datenschutz.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/agb',
      name: 'agb',
      component: () => import('./views/legal/AGB.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/widerruf',
      name: 'widerruf',
      component: () => import('./views/legal/Widerruf.vue'),
      meta: { requiresAuth: false }
    }
  ]
})

// Add route guards for authentication
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Check if route requires authentication
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth) {
    // Try to get current user
    const user = await authStore.getCurrentUser()
    
    if (!user) {
      // User is not authenticated, redirect to login
      console.log('User not authenticated, redirecting to login')
      next('/auth/login')
      return
    }
  }
  
  // User is authenticated or route doesn't require auth
  next()
})

const pinia = createPinia()
const app = createApp(App)

app.use(vuetify)
app.use(pinia) // Use pinia before router so stores are available in route guards
app.use(router)

// Initialize authentication state
const authStore = useAuthStore()
authStore.getCurrentUser().then(() => {
  console.log('Authentication state initialized')
}).catch(error => {
  console.log('Failed to initialize auth state:', error)
})

app.mount('#app')