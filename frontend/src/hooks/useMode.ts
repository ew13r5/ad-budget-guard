import { useMutation, useQueryClient } from '@tanstack/react-query'
import { setMode } from '@/api/mode'
import type { AccountMode } from '@/api/types'

export function useSetModeMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ accountId, mode }: { accountId: string; mode: AccountMode }) =>
      setMode(accountId, mode),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}
