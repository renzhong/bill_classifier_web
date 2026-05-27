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

export const assetApi = {
  list: (month?: string) => request.get<unknown, Asset[]>('/assets', { params: month ? { month } : {} }),
  create: (body: Omit<Asset, 'id'>) => request.post<unknown, Asset>('/assets', body),
  patch: (id: number, body: Partial<Asset>) => request.patch<unknown, Asset>(`/assets/${id}`, body),
  remove: (id: number) => request.delete<unknown, { deleted: number }>(`/assets/${id}`),
  copy: (from_month: string, to_month: string, overwrite = false) =>
    request.post<unknown, { copied: number; from: string; to: string }>('/assets/copy', { from_month, to_month, overwrite }),
}

export const incomeApi = {
  list: (q: { year?: string; month?: string } = {}) =>
    request.get<unknown, Income[]>('/incomes', { params: q }),
  create: (body: Omit<Income, 'id'>) => request.post<unknown, Income>('/incomes', body),
  patch: (id: number, body: Partial<Income>) => request.patch<unknown, Income>(`/incomes/${id}`, body),
  remove: (id: number) => request.delete<unknown, { deleted: number }>(`/incomes/${id}`),
}
