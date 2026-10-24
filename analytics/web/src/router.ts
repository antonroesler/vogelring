import { createRouter, createWebHashHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/start' },
    { path: '/start', component: () => import('./pages/StartPage.vue'), meta: { title: 'Start' } },
    { path: '/live', component: () => import('./pages/LivePage.vue'), meta: { title: 'Live' } },
    { path: '/erkunden/:viewId?', component: () => import('./pages/ErkundenPage.vue'), meta: { title: 'Daten erkunden' } },
    { path: '/ansichten', component: () => import('./pages/AnsichtenPage.vue'), meta: { title: 'Ansichten' } },
    { path: '/mappen', component: () => import('./pages/MappenPage.vue'), meta: { title: 'Mappen' } },
    { path: '/mappen/:id', component: () => import('./pages/MappeDetailPage.vue'), meta: { title: 'Mappe' } },
    { path: '/gruppen', component: () => import('./pages/GruppenPage.vue'), meta: { title: 'Gruppen' } },
    { path: '/gruppen/:id', component: () => import('./pages/GruppeDetailPage.vue'), meta: { title: 'Gruppe' } },
    { path: '/auswertungen', component: () => import('./pages/AuswertungenPage.vue'), meta: { title: 'Auswertungen' } },
    { path: '/auswertungen/:id', component: () => import('./pages/AuswertungDetailPage.vue'), meta: { title: 'Auswertung' } },
    { path: '/berichte', component: () => import('./pages/BerichtePage.vue'), meta: { title: 'Berichte & Präsentationen' } },
    { path: '/begriffe', component: () => import('./pages/BegriffePage.vue'), meta: { title: 'Begriffe' } },
    { path: '/notizen', component: () => import('./pages/NotizenPage.vue'), meta: { title: 'Notizen' } },
    { path: '/daten/:datasetId', component: () => import('./pages/DatenPage.vue'), meta: { title: 'Daten' } },
    { path: '/:pathMatch(.*)*', redirect: '/start' },
  ],
})

router.afterEach((to) => {
  document.title = `${to.meta.title ? to.meta.title + ' · ' : ''}Vogelring Analyse`
})
