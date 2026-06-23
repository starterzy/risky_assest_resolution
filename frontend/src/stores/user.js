import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userId = ref(Number(localStorage.getItem('userId')) || 0)
  const name = ref(localStorage.getItem('name') || '')
  const role = ref(localStorage.getItem('role') || '')

  function setLogin(data) {
    token.value = data.token
    userId.value = data.user_id
    name.value = data.name
    role.value = data.role
    localStorage.setItem('token', data.token)
    localStorage.setItem('userId', data.user_id)
    localStorage.setItem('name', data.name)
    localStorage.setItem('role', data.role)
  }

  function logout() {
    token.value = ''
    userId.value = 0
    name.value = ''
    role.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('userId')
    localStorage.removeItem('name')
    localStorage.removeItem('role')
  }

  const isAdmin = () => role.value === 'admin'

  return { token, userId, name, role, setLogin, logout, isAdmin }
})
