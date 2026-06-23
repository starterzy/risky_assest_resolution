import http from './index'

export const getPendingList = (period) => http.get('/api/approve/pending', { params: { period } })
export const approveOrReject = (recordId, data) => http.post(`/api/approve/records/${recordId}/action`, data)
export const getApprovedList = (period) => http.get('/api/approve/approved', { params: { period } })
export const groupModify = (recordId, data) => http.put(`/api/approve/records/${recordId}/group-modify`, data)
