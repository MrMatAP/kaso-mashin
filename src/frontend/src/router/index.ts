// Composables
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/default/Default.vue'),
    children: [
      {
        path: '/',
        name: 'Home',
        // route level code-splitting
        // this generates a separate chunk (Home-[hash].js) for this route
        // which is lazy-loaded when the route is visited.
        component: () => import('@/views/Home.vue'),
      },
      {
        path: '/instances',
        name: 'Instances',
        component: () => import('@/views/Instances.vue')
      },
      {
        path: '/identities',
        name: 'Identities',
        component: () => import('@/views/Identities.vue')
      },
      {
        path: '/networks',
        name: 'Networks',
        component: () => import('@/views/Networks.vue')
      },
      {
        path: '/images',
        name: 'Images',
        component: () => import('@/views/Images.vue')
      },
      {
        path: '/images-grid',
        name: 'Images-Grid',
        component: () => import('@/views/Images-Grid.vue')
      }
    ],
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
})

export default router
