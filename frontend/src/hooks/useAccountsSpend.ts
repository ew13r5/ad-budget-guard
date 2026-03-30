import { useQuery } from '@tanstack/react-query'
import { fetchSpend, type SpendData } from '@/api/monitoring'

export function useAccountsSpend(accountIds: string[]) {
  return useQuery({
    queryKey: ['accounts-spend', ...accountIds.sort()],
    queryFn: async () => {
      const results = await Promise.all(
        accountIds.map(async (id) => {
          try {
            const data = await fetchSpend(id)
            return { id, data: data[0] ?? null }
          } catch {
            return { id, data: null }
          }
        })
      )
      const mapped: Record<string, SpendData> = {}
      for (const r of results) {
        if (r.data) mapped[r.id] = r.data
      }
      return mapped
    },
    staleTime: 30_000,
    enabled: accountIds.length > 0,
  })
}
