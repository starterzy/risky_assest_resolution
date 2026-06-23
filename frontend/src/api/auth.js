import http from './index'

export function login(username, password) {
  return http.post('/api/auth/login', { username, password })
}
