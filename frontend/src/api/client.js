import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

export const getTenants = () => api.get('/api/tenants/').then(r => r.data)
export const getTenant = (id) => api.get(`/api/tenants/${id}`).then(r => r.data)

export const getLeads = (companyId) =>
  api.get('/api/leads/', { params: { company_id: companyId } }).then(r => r.data)

export const getLead = (id) => api.get(`/api/leads/${id}`).then(r => r.data)

export const getLeadCallLog = (customerId) =>
  api.get(`/api/leads/${customerId}/call-log`).then(r => r.data)

export const createLead = (data) => api.post('/api/leads/', data).then(r => r.data)

export const updateLead = (id, data) => api.patch(`/api/leads/${id}`, data).then(r => r.data)

export const resetLead = (id) => api.post(`/api/leads/${id}/reset`).then(r => r.data)

export const deleteLead = (id) => api.delete(`/api/leads/${id}`)

export const triggerCampaign = (companyId) =>
  api.post('/api/campaigns/trigger', { company_id: companyId }).then(r => r.data)

export const getCampaignStats = (companyId) =>
  api.get(`/api/campaigns/stats/${companyId}`).then(r => r.data)

export const testWebhook = (customerId, companyId) =>
  api.post('/api/webhooks/vapi/test', null, {
    params: { customer_id: customerId, company_id: companyId }
  }).then(r => r.data)

export default api
