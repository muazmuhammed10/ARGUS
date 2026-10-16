import apiClient from './api'
import type { DashboardSummary } from '../types'

export interface DashboardTrend {
  day: string
  critical: number
  high: number
  medium: number
  low: number
  info: number
}

export interface DashboardTrendsResponse {
  trend_data: DashboardTrend[]
  event_type_distribution: Array<{ type: string; count: number }>
  window_days: number
}

export const dashboardService = {
  async getSummary(days = 7): Promise<DashboardSummary & Record<string, number>> {
    const { data } = await apiClient.get('/dashboard/summary', { params: { days } })
    return data
  },

  async getTrends(days = 7): Promise<DashboardTrendsResponse> {
    const { data } = await apiClient.get('/dashboard/trends', { params: { days } })
    return data
  },

  async getRecentAlerts(limit = 10) {
    const { data } = await apiClient.get('/dashboard/alerts/recent', { params: { limit } })
    return data
  },
}
