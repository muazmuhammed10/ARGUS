import apiClient from './api'
import type { Investigation, PaginatedResponse } from '../types'

export const investigationsService = {
  async getInvestigations(params?: Record<string, unknown>): Promise<PaginatedResponse<Investigation>> {
    const { data } = await apiClient.get('/investigations', { params })
    return data
  },

  async getInvestigation(id: string): Promise<Investigation> {
    const { data } = await apiClient.get<Investigation>(`/investigations/${id}`)
    return data
  },

  async createInvestigation(payload: Partial<Investigation>): Promise<Investigation> {
    const { data } = await apiClient.post<Investigation>('/investigations', payload)
    return data
  },

  async updateInvestigation(id: string, payload: Partial<Investigation>): Promise<Investigation> {
    const { data } = await apiClient.patch<Investigation>(`/investigations/${id}`, payload)
    return data
  },

  async addNote(investigationId: string, content: string, note_type = 'OBSERVATION') {
    const { data } = await apiClient.post(`/investigations/${investigationId}/notes`, { content, note_type })
    return data
  },

  async getNotes(investigationId: string) {
    const { data } = await apiClient.get(`/investigations/${investigationId}/notes`)
    return data
  },
}
