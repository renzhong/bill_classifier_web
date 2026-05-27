import request from './request'

export interface StrategyTypeMeta {
  type_key: string
  display_name: string
  description: string
  param_schema: Record<string, unknown>
}

export interface PipelineStep {
  id: number
  strategy_type: string
  display_name: string
  params: Record<string, unknown>
  sort_order: number
  enabled: boolean
}

export const pipelineApi = {
  strategyTypes: () => request.get<unknown, StrategyTypeMeta[]>('/pipeline/strategy-types'),
  listSteps: () => request.get<unknown, PipelineStep[]>('/pipeline/steps'),
  createStep: (body: Omit<PipelineStep, 'id'>) =>
    request.post<unknown, PipelineStep>('/pipeline/steps', body),
  patchStep: (id: number, body: Partial<PipelineStep>) =>
    request.patch<unknown, PipelineStep>(`/pipeline/steps/${id}`, body),
  deleteStep: (id: number) =>
    request.delete<unknown, { deleted: number }>(`/pipeline/steps/${id}`),
  reorder: (order: Array<{ id: number; sort_order: number }>) =>
    request.post<unknown, { reordered: number }>('/pipeline/steps/reorder', { order }),
}
