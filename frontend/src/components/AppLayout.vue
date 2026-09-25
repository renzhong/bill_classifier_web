<script setup lang="ts">
import { computed, h, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import {
  NLayout, NLayoutSider, NLayoutHeader, NLayoutContent,
  NMenu, NSpace, NButton, NText, NAvatar, type MenuOption,
} from 'naive-ui'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const user = useUserStore()

onMounted(async () => {
  if (!user.profile) {
    try { await user.fetchMe() } catch { /* token 失效会被拦截器处理 */ }
  }
})

function link(label: string, to: string) {
  return () => h(RouterLink, { to }, { default: () => label })
}

const menuOptions = computed<MenuOption[]>(() => [
  { label: link('账单', '/bills'), key: 'bills' },
  { label: link('分类花费', '/reports/category'), key: 'reports.category' },
  { label: link('资产汇总', '/assets'), key: 'assets' },
  { label: link('投资', '/investments'), key: 'investments' },
  { label: link('收入', '/income'), key: 'income' },
  {
    label: '设置', key: 'settings', children: [
      { label: link('Tag 管理', '/settings/tags'), key: 'settings.tags' },
      { label: link('字典管理', '/settings/dicts'), key: 'settings.dicts' },
      { label: link('分类 Pipeline', '/settings/pipeline'), key: 'settings.pipeline' },
      { label: link('AI 凭据', '/settings/ai/credentials'), key: 'settings.ai.credentials' },
      { label: link('AI 策略', '/settings/ai/strategies'), key: 'settings.ai.strategies' },
      ...(user.profile?.is_admin
        ? [{ label: link('邀请码管理', '/settings/invitations'), key: 'settings.invitations' }]
        : []),
    ],
  },
])

const activeKey = computed(() => (route.name as string) || 'dashboard')

function logout() {
  user.clear()
  router.replace('/login')
}
</script>

<template>
  <n-layout class="app-shell" has-sider>
    <n-layout-sider bordered :width="220" collapse-mode="width" :collapsed-width="60">
      <div class="app-brand">Bill Classifier<small>个人财务工作台</small></div>
      <n-menu :value="activeKey" :options="menuOptions" :indent="18" :collapsed-width="60" :collapsed-icon-size="22" />
    </n-layout-sider>
    <n-layout>
      <n-layout-header bordered class="app-topbar">
        <n-text strong>{{ (route.meta.title as string) || '' }}</n-text>
        <n-space align="center">
          <n-avatar round size="small">{{ (user.profile?.nickname || user.profile?.email || '?')[0] }}</n-avatar>
          <n-text depth="2">{{ user.profile?.nickname || user.profile?.email }}</n-text>
          <n-button size="small" text @click="logout">退出</n-button>
        </n-space>
      </n-layout-header>
      <n-layout-content content-style="padding: 24px 30px 56px; overflow:auto">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>
