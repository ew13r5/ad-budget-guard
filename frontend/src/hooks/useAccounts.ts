import { useQuery } from '@tanstack/react-query'
import { fetchAccounts, fetchAccount, fetchCampaigns } from '@/api/accounts'

export function useAccounts() {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: fetchAccounts,
    staleTime: Infinity,
  })
}

export function useAccount(id: string) {
  return useQuery({
    queryKey: ['accounts', id],
    queryFn: () => fetchAccount(id),
    enabled: !!id,
  })
}

export function useAccountCampaigns(accountId: string) {
  return useQuery({
    queryKey: ['accounts', accountId, 'campaigns'],
    queryFn: () => fetchCampaigns(accountId),
    enabled: !!accountId,
  })
}
