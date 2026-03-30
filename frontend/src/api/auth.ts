import apiClient from './client'
import type { TokenResponse, UserResponse, DiscoverAccountsResponse, ImportCampaignsResponse } from './types'

export async function facebookLogin(): Promise<{ auth_url: string }> {
  const { data } = await apiClient.get<{ auth_url: string }>('/auth/facebook/login')
  return data
}

export async function facebookAuth(code: string, state?: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/facebook', { code, state })
  return data
}

export async function refreshToken(token: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/refresh', {
    refresh_token: token,
  })
  return data
}

export async function fetchMe(): Promise<UserResponse> {
  const { data } = await apiClient.get<UserResponse>('/auth/me')
  return data
}

export async function devLogin(): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/dev-login')
  return data
}

export async function discoverAccounts(): Promise<DiscoverAccountsResponse> {
  const { data } = await apiClient.post<DiscoverAccountsResponse>('/auth/facebook/discover-accounts')
  return data
}

export async function importCampaigns(accountId: string): Promise<ImportCampaignsResponse> {
  const { data } = await apiClient.post<ImportCampaignsResponse>('/auth/facebook/import-campaigns', {
    account_id: accountId,
  })
  return data
}
