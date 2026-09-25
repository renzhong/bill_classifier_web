import request from './request'

export type AssetType = 'cash' | 'deposit' | 'stock' | 'fund' | 'other'

export interface Asset {
  id: number
  snapshot_month: string
  asset_type: AssetType
  account_name: string
  amount: string
  remark: string | null
}

export interface Income {
  id: number
  year_month: string
  source: string
  amount: string
  remark: string | null
}

export const incomeApi = {
  list: (q: { year?: string; month?: string } = {}) =>
    request.get<unknown, Income[]>('/incomes', { params: q }),
  create: (body: Omit<Income, 'id'>) => request.post<unknown, Income>('/incomes', body),
  patch: (id: number, body: Partial<Income>) => request.patch<unknown, Income>(`/incomes/${id}`, body),
  remove: (id: number) => request.delete<unknown, { deleted: number }>(`/incomes/${id}`),
}

export interface AssetItem { id: number; name: string; kind: 'asset' | 'liability'; active: boolean; legacy_type: string | null }
export interface AssetMonthRow extends AssetItem { amount: string | null; remark: string | null; included_in_total: boolean }
export interface InvestmentItem { id: number; name: string; initial_principal: string; first_month: string; active: boolean; linked_asset_item_id: number | null }
export interface InvestmentMonthRow extends InvestmentItem {
  month: string; buys: string; sells: string; closing_value: string | null
  profit: string | null; missing_previous: boolean
}
export interface AssetMonthSummary {
  month: string; items: AssetMonthRow[]; investments: InvestmentMonthRow[]
  asset_total: string; liability_total: string; net_assets: string; complete: boolean
}
export interface InvestmentMonthSummary {
  month: string; items: InvestmentMonthRow[]; total_value: string; total_profit: string; complete: boolean
}
export interface IncomeEntry { id: number; occurred_at: string; amount: string; source: string | null; remark: string | null }
export interface IncomeSummary { year: number; month: string; month_total: string; year_total: string; legacy_monthly: Income[] }

export const assetItemApi = {
  list: () => request.get<unknown, AssetItem[]>('/asset-items'),
  create: (body: { name: string; kind: 'asset' | 'liability' }) => request.post<unknown, AssetItem>('/asset-items', body),
  patch: (id: number, body: { name?: string; active?: boolean }) => request.patch<unknown, AssetItem>(`/asset-items/${id}`, body),
  month: (month: string) => request.get<unknown, AssetMonthSummary>(`/asset-months/${month}`),
  value: (id: number, month: string, body: { amount: string; remark?: string | null }) =>
    request.put<unknown, AssetMonthRow>(`/asset-items/${id}/months/${month}`, body),
}

export const investmentApi = {
  list: () => request.get<unknown, InvestmentItem[]>('/investments'),
  create: (body: { name: string; initial_principal: string; first_month: string; linked_asset_item_id: number | null }) =>
    request.post<unknown, InvestmentItem>('/investments', body),
  patch: (id: number, body: { name?: string; initial_principal?: string; active?: boolean; linked_asset_item_id?: number | null }) =>
    request.patch<unknown, InvestmentItem>(`/investments/${id}`, body),
  month: (month: string) => request.get<unknown, InvestmentMonthSummary>(`/investments/months/${month}`),
  value: (id: number, month: string, body: { buys: string; sells: string; closing_value: string | null }) =>
    request.put<unknown, InvestmentMonthRow>(`/investments/${id}/months/${month}`, body),
}

export const incomeEntryApi = {
  list: (q: { month?: string; year?: number } = {}) => request.get<unknown, IncomeEntry[]>('/income-entries', { params: q }),
  create: (body: Omit<IncomeEntry, 'id'>) => request.post<unknown, IncomeEntry>('/income-entries', body),
  patch: (id: number, body: Partial<Omit<IncomeEntry, 'id'>>) =>
    request.patch<unknown, IncomeEntry>(`/income-entries/${id}`, body),
  remove: (id: number) => request.delete<unknown, { deleted: number }>(`/income-entries/${id}`),
  summary: (year: number, month: string) =>
    request.get<unknown, IncomeSummary>('/income-summary', { params: { year, month } }),
}
