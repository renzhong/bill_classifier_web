import request from './request'

export interface Category {
  id: number
  name: string
  display_name: string | null
  color: string | null
  sort_order: number
}

export interface Tag {
  id: number
  name: string
  color: string | null
}

export interface UserDict {
  id: number
  name: string
  target_field: 'payee' | 'item_name' | 'any'
  remark: string | null
  entry_count: number
}

export interface DictEntry {
  id: number
  key_text: string
  category_id: number
}

export const categoryApi = {
  list: () => request.get<unknown, Category[]>('/categories'),
  create: (body: Omit<Category, 'id'>) => request.post<unknown, Category>('/categories', body),
  patch: (id: number, body: Partial<Category>) => request.patch<unknown, Category>(`/categories/${id}`, body),
  remove: (id: number) => request.delete<unknown, { deleted: number }>(`/categories/${id}`),
  reorder: (order: Array<{ id: number; sort_order: number }>) =>
    request.post<unknown, { reordered: number }>('/categories/reorder', { order }),
}

export const tagApi = {
  list: () => request.get<unknown, Tag[]>('/tags'),
  create: (body: { name: string; color?: string | null }) => request.post<unknown, Tag>('/tags', body),
  remove: (id: number) => request.delete<unknown, { deleted: number }>(`/tags/${id}`),
}

export const dictApi = {
  list: () => request.get<unknown, UserDict[]>('/dicts'),
  create: (body: Omit<UserDict, 'id' | 'entry_count'>) => request.post<unknown, UserDict>('/dicts', body),
  patch: (id: number, body: Partial<UserDict>) => request.patch<unknown, UserDict>(`/dicts/${id}`, body),
  remove: (id: number) => request.delete<unknown, { deleted: number }>(`/dicts/${id}`),
  listEntries: (id: number) => request.get<unknown, DictEntry[]>(`/dicts/${id}/entries`),
  addEntry: (id: number, body: { key_text: string; category_id: number }) =>
    request.post<unknown, DictEntry>(`/dicts/${id}/entries`, body),
  removeEntry: (id: number, entryId: number) =>
    request.delete<unknown, { deleted: number }>(`/dicts/${id}/entries/${entryId}`),
  bulkImport: (id: number, csv_text: string) =>
    request.post<unknown, { inserted: number }>(`/dicts/${id}/entries/bulk`, { csv_text }),
}
