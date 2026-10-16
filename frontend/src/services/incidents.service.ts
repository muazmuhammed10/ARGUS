import apiClient from './api'
import type { Incident, PaginatedResponse } from '../types'

export interface IncidentCreatePayload {
  title: string
  description: string
  severity: string
  assigned_to_id?: string
}

export interface IncidentUpdatePayload {
  title?: string
  description?: string
  severity?: string
  status?: string
  assigned_to_id?: string
  remediation_summary?: string
  resolution_summary?: string
}

export const incidentsService = {
  async getIncidents(params?: Record<string, unknown>): Promise<PaginatedResponse<Incident>> {
    const { data } = await apiClient.get('/incidents', { params })
    return data
  },

  async getIncident(id: string): Promise<Incident> {
    const { data } = await apiClient.get<Incident>(`/incidents/${id}`)
    return data
  },

  async createIncident(payload: IncidentCreatePayload): Promise<Incident> {
    const { data } = await apiClient.post<Incident>('/incidents', payload)
    return data
  },

  async updateIncident(id: string, payload: IncidentUpdatePayload): Promise<Incident> {
    const { data } = await apiClient.patch<Incident>(`/incidents/${id}`, payload)
    return data
  },

  async linkEvent(incidentId: string, eventId: string, note?: string): Promise<void> {
    await apiClient.post(`/incidents/${incidentId}/events/${eventId}`, null, {
      params: note ? { note } : undefined,
    })
  },

  async getIncidentEvents(incidentId: string) {
    const { data } = await apiClient.get(`/incidents/${incidentId}/events`)
    return data
  },
}
