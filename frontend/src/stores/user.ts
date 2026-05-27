import { defineStore } from 'pinia'
import { authApi, type UserInfo } from '@/api/auth'

const TOKEN_KEY = 'bcw_access_token'
const REFRESH_KEY = 'bcw_refresh_token'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    refreshToken: localStorage.getItem(REFRESH_KEY) || '',
    profile: null as UserInfo | null,
  }),
  actions: {
    setTokens(access: string, refresh: string) {
      this.token = access
      this.refreshToken = refresh
      localStorage.setItem(TOKEN_KEY, access)
      localStorage.setItem(REFRESH_KEY, refresh)
    },
    async fetchMe() {
      this.profile = await authApi.me()
      return this.profile
    },
    clear() {
      this.token = ''
      this.refreshToken = ''
      this.profile = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_KEY)
    },
  },
})
