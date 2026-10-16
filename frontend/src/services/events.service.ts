import apiClient from './api'
import type { SecurityEvent, PaginatedResponse } from '../types'

export interface EventsQuery {
  page?: number
  page_size?: number
  severity?: string
  event_type?: string
  search?: string
}

export const eventsService = {
  async getEvents(params?: EventsQuery): Promise<PaginatedResponse<SecurityEvent>> {
    const { data } = await apiClient.get('/events', { params })
    return data
  },

  async getEvent(id: string): Promise<SecurityEvent> {
    const { data } = await apiClient.get<SecurityEvent>(`/events/${id}`)
    return data
  },
}
