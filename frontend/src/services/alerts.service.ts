import apiClient from './api'

export const alertsService = {
  async getAlerts(params?: Record<string, unknown>) {
    const { data } = await apiClient.get('/alerts', { params })
    return data
  },

  async updateAlertStatus(id: string, status: string) {
    const { data } = await apiClient.patch(`/alerts/${id}`, { status })
    return data
  },
}
