import apiClient from './client'
import type { AccountMode, ModeResponse } from './types'

export async function getMode(accountId: string): Promise<ModeResponse> {
  const { data } = await apiClient.get<ModeResponse>('/mode', {
    params: { account_id: accountId },
  })
  return data
}

export async function setMode(accountId: string, mode: AccountMode): Promise<ModeResponse> {
  const { data } = await apiClient.put<ModeResponse>('/mode', {
    account_id: accountId,
    mode,
  })
  return data
}
