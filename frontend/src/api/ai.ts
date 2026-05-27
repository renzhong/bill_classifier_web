import request from './request'

export interface ProviderMeta {
  provider_key: string
  display_name: string
  default_base_url: string | null
  suggested_models: string[]
}

export interface AiCredential {
  id: number
  provider: string
  model_name: string
  base_url: string | null
  enabled: boolean
  has_api_key: boolean
  created_at: string
}

export interface AiStrategy {
  id: number
  name: string
  strategy_text: string
  active: boolean
  credential_id: number | null
  created_at: string
  updated_at: string
}

export const aiApi = {
  providers: () => request.get<unknown, ProviderMeta[]>('/ai/providers'),

  listCredentials: () => request.get<unknown, AiCredential[]>('/ai/credentials'),
  createCredential: (body: {
    provider: string; model_name: string; api_key: string; base_url?: string | null; enabled?: boolean
  }) => request.post<unknown, AiCredential>('/ai/credentials', body),
  patchCredential: (id: number, body: Partial<{ model_name: string; api_key: string; base_url: string | null; enabled: boolean }>) =>
    request.patch<unknown, AiCredential>(`/ai/credentials/${id}`, body),
  deleteCredential: (id: number) =>
    request.delete<unknown, { deleted: number }>(`/ai/credentials/${id}`),

  listStrategies: () => request.get<unknown, AiStrategy[]>('/ai/strategies'),
  createStrategy: (body: Partial<AiStrategy>) =>
    request.post<unknown, AiStrategy>('/ai/strategies', body),
  patchStrategy: (id: number, body: Partial<AiStrategy>) =>
    request.patch<unknown, AiStrategy>(`/ai/strategies/${id}`, body),
  deleteStrategy: (id: number) =>
    request.delete<unknown, { deleted: number }>(`/ai/strategies/${id}`),

  preview: (strategy_text: string) =>
    request.post<unknown, { prompt: string }>('/ai/strategies/preview', { strategy_text }),

  test: (body: { credential_id: number; strategy_id?: number | null; sample: Record<string, unknown> }) =>
    request.post<unknown, { category: string | null; confidence: string | null; raw: string }>('/ai/test', body),
}
