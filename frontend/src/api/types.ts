export const AccountMode = {
  sandbox: 'sandbox',
  simulation: 'simulation',
  production: 'production',
} as const
export type AccountMode = (typeof AccountMode)[keyof typeof AccountMode]

export const CampaignStatus = {
  ACTIVE: 'ACTIVE',
  PAUSED: 'PAUSED',
} as const
export type CampaignStatus = (typeof CampaignStatus)[keyof typeof CampaignStatus]

export const UserRole = {
  owner: 'owner',
  manager: 'manager',
  viewer: 'viewer',
} as const
export type UserRole = (typeof UserRole)[keyof typeof UserRole]

// --- Response interfaces ---

export interface AdAccountResponse {
  id: string
  meta_account_id: string
  name: string
  mode: AccountMode
  currency: string
  timezone: string
  is_active: boolean
  created_at: string
}

export interface AdAccountListResponse {
  accounts: AdAccountResponse[]
  total: number
}

export interface CampaignResponse {
  id: string
  meta_campaign_id: string
  name: string
  status: CampaignStatus
  daily_budget: string | null
  lifetime_budget: string | null
}

export interface CampaignListResponse {
  campaigns: CampaignResponse[]
  total: number
}

export interface ActionResult {
  success: boolean
  message: string
  campaign_id: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  name: string
  email: string | null
  needs_reauth: boolean
}

export interface ModeUpdateRequest {
  account_id: string
  mode: AccountMode
}

export interface ModeResponse {
  account_id: string
  mode: AccountMode
}

// --- Simulation types ---

export interface SimulationStartRequest {
  scenario: string
}

export interface SimulationStartResponse {
  status: string
  scenario: string
  speed: number
}

export interface SimulationPauseResponse {
  status: string
}

export interface SimulationSpeedRequest {
  multiplier: 1 | 5 | 10
}

export interface SimulationSpeedResponse {
  speed: number
}

export interface SimulationScenarioRequest {
  scenario: string
}

export interface SimulationScenarioResponse {
  scenario: string
  status: string
}

export interface SimulationTriggerAnomalyRequest {
  campaign_id: string
}

export interface SimulationTriggerAnomalyResponse {
  triggered: boolean
  campaign_id: string
}

export interface SimulationResetResponse {
  status: string
  message: string
}

export interface SimulationStatusResponse {
  status: string
  sim_time: string | null
  speed: number
  scenario: string
  tick_count: number
  campaign_count: number
}

export interface SimulationLogEntry {
  id: string
  event_type: string
  campaign_id: string | null
  sim_time: string
  real_time: string
  details: Record<string, unknown> | null
}

export interface SimulationLogResponse {
  entries: SimulationLogEntry[]
  total: number
  limit: number
  offset: number
}

// --- WebSocket message types ---

export interface WsStateSnapshot {
  type: 'state_snapshot'
  sim_time: string
  status: 'running' | 'paused' | 'stopped'
  speed: 1 | 5 | 10
  scenario: string
  tick_count: number
}

export interface WsTickCampaign {
  campaign_id: string
  total_spend: string
  delta_spend: string
  budget_percent: string
  status: 'ACTIVE' | 'PAUSED'
}

export interface WsTickUpdate {
  type: 'tick_update'
  sim_time: string
  tick_count: number
  campaigns: WsTickCampaign[]
}

export interface WsSimEvent {
  type: 'sim_event'
  event: string
  campaign_id: string
  reason: string
  sim_time: string
}

export type WsMessage = WsStateSnapshot | WsTickUpdate | WsSimEvent

// --- OAuth Discovery/Import types ---

export interface DiscoveredAccount {
  id: string
  meta_account_id: string
  name: string
  currency: string
  timezone: string
  is_new: boolean
}

export interface DiscoverAccountsResponse {
  accounts: DiscoveredAccount[]
  total: number
}

export interface ImportCampaignsResponse {
  imported: number
  updated: number
  total: number
}
