import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'
import Login from '../views/Login.vue'
import Layout from '../views/Layout.vue'
import FillForm from '../views/FillForm.vue'
import ApprovalList from '../views/ApprovalList.vue'
import DataView from '../views/DataView.vue'
import Admin from '../views/Admin.vue'

const routes = [
  { path: '/login', component: Login },
  {
    path: '/',
    component: Layout,
    children: [
      { path: '', redirect: '/fill' },
      { path: 'fill', component: FillForm },
      { path: 'approve', component: ApprovalList },
      { path: 'data', component: DataView },
      { path: 'admin', component: Admin },
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const store = useUserStore()
  if (to.path !== '/login' && !store.token) return '/login'
})

export default router
