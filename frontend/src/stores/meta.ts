import { defineStore } from 'pinia'
import { categoryApi, tagApi, dictApi, type Category, type Tag, type UserDict } from '@/api/meta'

export const useMetaStore = defineStore('meta', {
  state: () => ({
    categories: [] as Category[],
    tags: [] as Tag[],
    dicts: [] as UserDict[],
    loaded: false,
  }),
  getters: {
    categoryMap: (s) => new Map(s.categories.map((c) => [c.id, c])),
    tagMap: (s) => new Map(s.tags.map((t) => [t.id, t])),
  },
  actions: {
    async loadAll(force = false) {
      if (this.loaded && !force) return
      const [c, t, d] = await Promise.all([categoryApi.list(), tagApi.list(), dictApi.list()])
      this.categories = c
      this.tags = t
      this.dicts = d
      this.loaded = true
    },
    async reloadCategories() { this.categories = await categoryApi.list() },
    async reloadTags() { this.tags = await tagApi.list() },
    async reloadDicts() { this.dicts = await dictApi.list() },
  },
})
