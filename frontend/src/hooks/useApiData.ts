import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useFilterStore } from '../store/filterStore'

export function useDistricts() {
  return useQuery({ queryKey: ['districts'], queryFn: api.districts, staleTime: Infinity })
}

export function useSummary() {
  const date = useFilterStore((s) => s.selectedDate)
  return useQuery({
    queryKey: ['summary', date],
    queryFn: () => api.summary(date ?? undefined),
  })
}

export function useStock(extra?: { block_code?: string; fertilizer_name?: string; limit?: number }) {
  const district = useFilterStore((s) => s.selectedDistrictCode)
  const date = useFilterStore((s) => s.selectedDate)
  return useQuery({
    queryKey: ['stock', district, date, extra],
    queryFn: () => api.stock({ district_code: district ?? undefined, scrape_date: date ?? undefined, ...extra }),
  })
}

export function useDealerDetails(dealer_code: string) {
  return useQuery({
    queryKey: ['dealer', dealer_code],
    queryFn: () => api.dealerDetails(dealer_code),
    enabled: !!dealer_code,
  })
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    refetchInterval: 30_000,
  })
}
