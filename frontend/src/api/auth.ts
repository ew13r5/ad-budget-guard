import apiClient from './client'
import type { TokenResponse, UserResponse } from './types'

export async function facebookAuth(code: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/facebook', { code })
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
