import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  { path: '/register', name: 'register', component: () => import('@/views/Register.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/components/AppLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'bills/upload', name: 'bills.upload', component: () => import('@/views/Placeholder.vue'), meta: { title: '上传账单' } },
      { path: 'bills/tasks', name: 'bills.tasks', component: () => import('@/views/Placeholder.vue'), meta: { title: '上传任务' } },
      { path: 'bills/detail', name: 'bills.detail', component: () => import('@/views/Placeholder.vue'), meta: { title: '账单明细' } },
      { path: 'reports/yearly', name: 'reports.yearly', component: () => import('@/views/Placeholder.vue'), meta: { title: '全年收支' } },
      { path: 'reports/monthly', name: 'reports.monthly', component: () => import('@/views/Placeholder.vue'), meta: { title: '单月汇总' } },
      { path: 'reports/category', name: 'reports.category', component: () => import('@/views/Placeholder.vue'), meta: { title: '分类汇总' } },
      { path: 'settings/categories', name: 'settings.categories', component: () => import('@/views/Placeholder.vue'), meta: { title: '类别管理' } },
      { path: 'settings/tags', name: 'settings.tags', component: () => import('@/views/Placeholder.vue'), meta: { title: 'Tag 管理' } },
      { path: 'settings/dicts', name: 'settings.dicts', component: () => import('@/views/Placeholder.vue'), meta: { title: '字典管理' } },
      { path: 'settings/pipeline', name: 'settings.pipeline', component: () => import('@/views/Placeholder.vue'), meta: { title: '分类 Pipeline' } },
      { path: 'settings/ai/credentials', name: 'settings.ai.credentials', component: () => import('@/views/Placeholder.vue'), meta: { title: 'AI 凭据' } },
      { path: 'settings/ai/strategies', name: 'settings.ai.strategies', component: () => import('@/views/Placeholder.vue'), meta: { title: 'AI 策略' } },
      { path: 'settings/assets', name: 'settings.assets', component: () => import('@/views/Placeholder.vue'), meta: { title: '资产录入' } },
      { path: 'settings/incomes', name: 'settings.incomes', component: () => import('@/views/Placeholder.vue'), meta: { title: '收入录入' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const user = useUserStore()
  if (!to.meta.public && !user.token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.public && user.token && (to.name === 'login' || to.name === 'register')) {
    return { name: 'dashboard' }
  }
})

export default router
