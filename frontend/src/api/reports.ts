import request from './request'

export interface MonthBucket {
  year_month: string
  income: string
  expense: string
  balance: string
}

export interface YearlyReport {
  year: number
  buckets: MonthBucket[]
  total_income: string
  total_expense: string
  total_balance: string
}

export interface CategoryBucket {
  category_id: number | null
  category_name: string | null
  amount: string
  count: number
  percent: number
}

export interface CategorySummary {
  year_month: string
  total_expense: string
  buckets: CategoryBucket[]
}

export interface AssetBucket {
  asset_type: string
  amount: string
  count: number
}

export interface BalanceReport {
  year_month: string
  asset_total: string
  buckets: AssetBucket[]
}

export interface MonthlyOverview {
  year_month: string
  bill_expense: string
  bill_income: string
  declared_income: string
  asset_total: string
  net_worth_change: string
}

export const reportApi = {
  yearly: (year: number) => request.get<unknown, YearlyReport>('/reports/yearly', { params: { year } }),
  monthly: (month: string) => request.get<unknown, MonthlyOverview>('/reports/monthly', { params: { month } }),
  categorySummary: (month: string) =>
    request.get<unknown, CategorySummary>('/reports/category-summary', { params: { month } }),
  balance: (month: string) => request.get<unknown, BalanceReport>('/reports/balance', { params: { month } }),
}
