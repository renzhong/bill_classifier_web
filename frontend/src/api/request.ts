import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import { useUserStore } from '@/stores/user'

export interface ApiEnvelope<T = unknown> {
  code: number
  msg: string
  data: T
}

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const user = useUserStore()
  if (user.token) {
    config.headers.Authorization = `Bearer ${user.token}`
  }
  return config
})

request.interceptors.response.use(
  (resp: AxiosResponse<ApiEnvelope>) => {
    const body = resp.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code !== 0) {
        return Promise.reject(new Error(body.msg || 'request failed'))
      }
      return body.data as never
    }
    return resp.data as never
  },
  (error) => {
    const status = error?.response?.status
    if (status === 401) {
      const user = useUserStore()
      user.clear()
      if (location.pathname !== '/login') {
        location.replace(`/login?redirect=${encodeURIComponent(location.pathname)}`)
      }
    }
    const msg = error?.response?.data?.msg || error.message || 'network error'
    return Promise.reject(new Error(msg))
  },
)

export default request
