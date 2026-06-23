import http from './index'

export const listUsers = () => http.get('/api/admin/users')
export const createUser = (data) => http.post('/api/admin/users', data)
export const updateUser = (id, data) => http.put(`/api/admin/users/${id}`, data)

export const listRiskItems = () => http.get('/api/admin/risk-items')
export const updateRiskItem = (id, data) => http.put(`/api/admin/risk-items/${id}`, data)
export const getFillPermissions = (riskItemId) => http.get(`/api/admin/fill-permissions/${riskItemId}`)
export const setFillPermissions = (riskItemId, userIds) => http.put(`/api/admin/fill-permissions/${riskItemId}`, { user_ids: userIds })
export const getApprovalChain = (riskItemId) => http.get(`/api/admin/approval-chains/${riskItemId}`)
export const setApprovalChain = (riskItemId, chains) => http.put(`/api/admin/approval-chains/${riskItemId}`, { chains })
