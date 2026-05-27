<script setup lang="ts">
import { computed, h, ref, onMounted } from 'vue'
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

const menuOptions = ref<MenuOption[]>([
  { label: link('概览', '/dashboard'), key: 'dashboard' },
  {
    label: '账单', key: 'bills', children: [
      { label: link('上传账单', '/bills/upload'), key: 'bills.upload' },
      { label: link('上传任务', '/bills/tasks'), key: 'bills.tasks' },
      { label: link('账单明细', '/bills/detail'), key: 'bills.detail' },
    ],
  },
  {
    label: '报表', key: 'reports', children: [
      { label: link('全年收支', '/reports/yearly'), key: 'reports.yearly' },
      { label: link('单月汇总', '/reports/monthly'), key: 'reports.monthly' },
      { label: link('分类汇总', '/reports/category'), key: 'reports.category' },
    ],
  },
  {
    label: '设置', key: 'settings', children: [
      { label: link('类别管理', '/settings/categories'), key: 'settings.categories' },
      { label: link('Tag 管理', '/settings/tags'), key: 'settings.tags' },
      { label: link('字典管理', '/settings/dicts'), key: 'settings.dicts' },
      { label: link('分类 Pipeline', '/settings/pipeline'), key: 'settings.pipeline' },
      { label: link('AI 凭据', '/settings/ai/credentials'), key: 'settings.ai.credentials' },
      { label: link('AI 策略', '/settings/ai/strategies'), key: 'settings.ai.strategies' },
      { label: link('资产录入', '/settings/assets'), key: 'settings.assets' },
      { label: link('收入录入', '/settings/incomes'), key: 'settings.incomes' },
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
  <n-layout style="height: 100vh" has-sider>
    <n-layout-sider bordered :width="220" collapse-mode="width" :collapsed-width="60">
      <div style="padding: 16px; font-weight: 600; font-size: 16px">Bill Classifier</div>
      <n-menu :value="activeKey" :options="menuOptions" :indent="18" :collapsed-width="60" :collapsed-icon-size="22" />
    </n-layout-sider>
    <n-layout>
      <n-layout-header bordered style="padding: 12px 24px; display: flex; align-items: center; justify-content: space-between">
        <n-text strong>{{ (route.meta.title as string) || '' }}</n-text>
        <n-space align="center">
          <n-avatar round size="small">{{ (user.profile?.nickname || user.profile?.email || '?')[0] }}</n-avatar>
          <n-text depth="2">{{ user.profile?.nickname || user.profile?.email }}</n-text>
          <n-button size="small" text @click="logout">退出</n-button>
        </n-space>
      </n-layout-header>
      <n-layout-content content-style="padding: 24px">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>
