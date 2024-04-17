import { createRouter, createWebHistory } from 'vue-router'
import config from "@/config";
import pageHome from '@/pages/page-home/page-home.vue'

const router = createRouter({
  history: createWebHistory(config.baseUrl),
  routes: [
    {
      path: '/',
      name: 'home',
      component: pageHome
    },
  ]
})

export default router
