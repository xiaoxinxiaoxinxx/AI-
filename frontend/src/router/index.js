import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'patients',
        name: 'Patients',
        component: () => import('../views/Patients.vue'),
        meta: { title: '患者管理' }
      },
      {
        path: 'prediction',
        name: 'Prediction',
        component: () => import('../views/Prediction.vue'),
        meta: { title: '风险预测' }
      },
      {
        path: 'training',
        name: 'Training',
        component: () => import('../views/Training.vue'),
        meta: { title: '联邦训练' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 未登录重定向到登录页
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('user')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router