const routes = [
  {
    path: '/statistics',
    component: () => import('@/views/Statistics.vue'),
    children: [
      {
        path: '',
        name: 'statistics-dashboard',
        component: () => import('@/views/statistics/DashboardView.vue')
      },
      {
        path: 'friends',
        name: 'statistics-friends',
        component: () => import('@/views/statistics/FriendsView.vue')
      },
      {
        path: 'radius',
        name: 'statistics-radius',
        component: () => import('@/views/statistics/RadiusView.vue')
      },
      {
        path: 'seasonal',
        name: 'statistics-seasonal',
        component: () => import('@/views/statistics/SeasonalAnalysisView.vue')
      }
    ]
  },
  {
    path: '/birds/:ring/environment-analysis',
    name: 'environment-analysis',
    component: () => import('@/views/EnvironmentAnalysis.vue')
  }
  // ... other routes
]; 