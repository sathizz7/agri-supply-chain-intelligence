export interface District {
  id: number
  code: string
  name_ta: string
}

export interface Block {
  id: number
  code: string
  name_ta: string
  district_code: string
}

export interface StockRecord {
  dealer_code: string
  dealer_name: string
  block_code: string
  block_name: string
  district_code: string
  district_name: string
  fertilizer_name: string
  quantity: number
  unit: string
  scrape_date: string
}

export interface StockItem {
  fertilizer_name: string
  quantity: number
  unit: string
  scrape_date: string
}

export interface DealerDetail {
  id: number
  dealer_code: string
  name_ta: string
  address: string | null
  contact: string | null
  block_name: string
  district_name: string
  stock_history: StockItem[]
}

export interface DistrictSummary {
  district_code: string
  district_name: string
  total_dealers: number
  total_stock_kg: number
  last_scraped: string | null
}
