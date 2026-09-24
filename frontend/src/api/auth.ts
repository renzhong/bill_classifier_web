import request from './request'

export interface LoginPayload { email: string; password: string }
export interface RegisterPayload { email: string; password: string; nickname?: string; invitation_code: string }

export interface TokenPair { access_token: string; refresh_token: string; token_type: string }
export interface UserInfo {
  id: number
  email: string
  nickname: string | null
  is_admin: boolean
  status: string
  created_at: string
}

export interface Invitation {
  id: number
  code: string
  max_uses: number
  used_count: number
  expires_at: string | null
  revoked_at: string | null
  created_at: string
}

export const authApi = {
  login: (payload: LoginPayload) => request.post<unknown, TokenPair>('/auth/login', payload),
  register: (payload: RegisterPayload) => request.post<unknown, UserInfo>('/auth/register', payload),
  me: () => request.get<unknown, UserInfo>('/auth/me'),
  refresh: (refresh_token: string) =>
    request.post<unknown, { access_token: string }>('/auth/refresh', { refresh_token }),
  listInvitations: () => request.get<unknown, Invitation[]>('/auth/invitations'),
  createInvitation: (body: { max_uses: number; expires_at?: string | null }) =>
    request.post<unknown, Invitation>('/auth/invitations', body),
  revokeInvitation: (id: number) =>
    request.post<unknown, Invitation>(`/auth/invitations/${id}/revoke`),
}
