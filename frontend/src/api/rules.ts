import apiClient from './client'

export interface Rule {
  id: string
  name: string
  type: string
  condition: string
  action: string
  is_active: boolean
  account_id: string | null
}

export interface RuleListResponse {
  rules: Rule[]
  total: number
}

export async function fetchRules(): Promise<RuleListResponse> {
  const { data } = await apiClient.get<RuleListResponse>('/rules')
  return data
}

export async function createRule(rule: Omit<Rule, 'id'>): Promise<Rule> {
  const { data } = await apiClient.post<Rule>('/rules', rule)
  return data
}

export async function updateRule(id: string, rule: Partial<Rule>): Promise<Rule> {
  const { data } = await apiClient.put<Rule>(`/rules/${id}`, rule)
  return data
}

export async function deleteRule(id: string): Promise<void> {
  await apiClient.delete(`/rules/${id}`)
}
