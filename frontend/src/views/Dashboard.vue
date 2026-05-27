<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NCard, NGrid, NGi, NSpace, NTag, NEmpty } from 'naive-ui'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const ready = ref(false)

onMounted(async () => {
  if (!user.profile) await user.fetchMe()
  ready.value = true
})
</script>

<template>
  <n-space vertical size="large">
    <n-card title="欢迎">
      <template v-if="ready && user.profile">
        当前用户：<strong>{{ user.profile.nickname || user.profile.email }}</strong>
        <n-tag v-if="user.profile.is_admin" type="warning" style="margin-left: 8px">admin</n-tag>
      </template>
    </n-card>

    <n-grid :cols="3" x-gap="16">
      <n-gi>
        <n-card title="本月支出">
          <n-empty description="尚无数据，先去上传账单" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="本月收入">
          <n-empty description="尚无数据" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="结余">
          <n-empty description="尚无数据" />
        </n-card>
      </n-gi>
    </n-grid>

    <n-card title="下一步建议">
      <ul>
        <li>到「类别管理」创建你的业务分类</li>
        <li>到「字典管理」批量录入关键词 → 类别映射</li>
        <li>到「分类 Pipeline」编排你的策略流</li>
        <li>到「上传账单」上传支付宝 / 微信账单</li>
      </ul>
    </n-card>
  </n-space>
</template>
