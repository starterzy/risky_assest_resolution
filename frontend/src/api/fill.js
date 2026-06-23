import http from './index'

export const getMyFillItems = (period) => http.get('/api/fill/my-items', { params: { period } })
export const saveFillRecord = (data) => http.post('/api/fill/records', data)
export const submitFillRecord = (id) => http.post(`/api/fill/records/${id}/submit`)
