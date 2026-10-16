import apiClient from './api'
import type { Asset, PaginatedResponse } from '../types'

export const assetsService = {
  async getAssets(params?: Record<string, unknown>): Promise<PaginatedResponse<Asset>> {
    const { data } = await apiClient.get('/assets', { params })
    return data
  },

  async getAsset(id: string): Promise<Asset> {
    const { data } = await apiClient.get<Asset>(`/assets/${id}`)
    return data
  },

  async createAsset(payload: Partial<Asset>): Promise<Asset> {
    const { data } = await apiClient.post<Asset>('/assets', payload)
    return data
  },

  async updateAsset(id: string, payload: Partial<Asset>): Promise<Asset> {
    const { data } = await apiClient.patch<Asset>(`/assets/${id}`, payload)
    return data
  },

  async deleteAsset(id: string): Promise<void> {
    await apiClient.delete(`/assets/${id}`)
  },
}
