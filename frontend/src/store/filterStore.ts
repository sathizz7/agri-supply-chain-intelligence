import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

interface FilterState {
  selectedDate: string | null
  selectedDistrictCode: string | null
  lowStockThreshold: number
  setDate: (date: string | null) => void
  setDistrict: (code: string | null) => void
  setThreshold: (t: number) => void
}

export const useFilterStore = create<FilterState>()(
  subscribeWithSelector((set) => ({
    selectedDate: null,
    selectedDistrictCode: null,
    lowStockThreshold: 500,
    setDate: (date) => set({ selectedDate: date }),
    setDistrict: (code) => set({ selectedDistrictCode: code }),
    setThreshold: (t) => set({ lowStockThreshold: t }),
  }))
)
