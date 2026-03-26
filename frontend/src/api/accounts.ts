import apiClient from './client'
import type { AdAccountListResponse, AdAccountResponse, CampaignListResponse, ActionResult } from './types'

export async function fetchAccounts(): Promise<AdAccountListResponse> {
  const { data } = await apiClient.get<AdAccountListResponse>('/accounts')
  return data
}

export async function fetchAccount(id: string): Promise<AdAccountResponse> {
  const { data } = await apiClient.get<AdAccountResponse>(`/accounts/${id}`)
  return data
}

export async function fetchCampaigns(accountId: string): Promise<CampaignListResponse> {
  const { data } = await apiClient.get<CampaignListResponse>(`/accounts/${accountId}/campaigns`)
  return data
}

export async function pauseCampaign(campaignId: string): Promise<ActionResult> {
  const { data } = await apiClient.post<ActionResult>(`/campaigns/${campaignId}/pause`)
  return data
}

export async function resumeCampaign(campaignId: string): Promise<ActionResult> {
  const { data } = await apiClient.post<ActionResult>(`/campaigns/${campaignId}/resume`)
  return data
}
