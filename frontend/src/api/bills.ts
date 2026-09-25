import request from './request'

export interface Bill {
  id: number
  source: string
  owner: string | null
  order_id: string | null
  payee: string | null
  item_name: string | null
  amount: string
  bill_type: string
  bill_time: string
  bill_month: string | null
  category_id: number | null
  classify_strategy_id: number | null
  classify_strategy_type: string | null
  lifecycle: string
  skip_reason: string | null
  ai_provider: string | null
  ai_confidence: string | null
  manual_overridden: boolean
  archived: boolean
  tag_ids: number[]
}

export interface BillListResult {
  items: Bill[]
  total: number
  page: number
  page_size: number
}

export interface BillListQuery {
  month?: string
  source?: string
  category_id?: number
  unclassified?: boolean
  tag_id?: number
  keyword?: string
  lifecycle?: string
  report_expense?: boolean
  page?: number
  page_size?: number
}

export interface UploadTask {
  id: number
  source: string
  filename: string
  file_size: number
  status: string
  total_rows: number
  classified_rows: number
  error_msg: string | null
  parse_errors: string[]
  tag_ids: number[]
  owner_label: string | null
  created_at: string
  finished_at: string | null
}

export const billApi = {
  upload: (form: FormData) => request.post<unknown, UploadTask>('/bills/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  list: (q: BillListQuery = {}) => request.get<unknown, BillListResult>('/bills', { params: q }),
  get: (id: number) => request.get<unknown, Bill>(`/bills/${id}`),
  patch: (id: number, body: { category_id: number | null }) =>
    request.patch<unknown, Bill>(`/bills/${id}`, body),
  reclassify: (id: number) =>
    request.post<unknown, { queued: boolean; note?: string }>(`/bills/${id}/reclassify`),
  batch: (body: { ids: number[]; action: string; payload?: Record<string, unknown> }) =>
    request.post<unknown, { affected: number }>('/bills/batch', body),
}

export const uploadTaskApi = {
  list: () => request.get<unknown, UploadTask[]>('/upload-tasks'),
  get: (id: number) => request.get<unknown, UploadTask>(`/upload-tasks/${id}`),
  bills: (id: number, page = 1, page_size = 50) =>
    request.get<unknown, BillListResult>(`/upload-tasks/${id}/bills`, { params: { page, page_size } }),
  classify: (id: number) => request.post<unknown, UploadTask>(`/upload-tasks/${id}/classify`),
  archive: (id: number) => request.post<unknown, UploadTask>(`/upload-tasks/${id}/archive`),
}
