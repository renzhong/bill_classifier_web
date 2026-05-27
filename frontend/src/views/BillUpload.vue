<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NCard, NForm, NFormItem, NSelect, NInput, NButton, NSpace,
  NUpload, useMessage, type UploadFileInfo, type UploadCustomRequestOptions,
} from 'naive-ui'
import { useMetaStore } from '@/stores/meta'
import { billApi } from '@/api/bills'

const message = useMessage()
const meta = useMetaStore()

const form = ref({
  source: 'alipay' as 'alipay' | 'wechat',
  owner_label: '',
  tag_ids: [] as number[],
})
const fileList = ref<UploadFileInfo[]>([])
const submitting = ref(false)

onMounted(async () => {
  await meta.loadAll()
})

const sourceOptions = [
  { label: '支付宝', value: 'alipay' },
  { label: '微信支付', value: 'wechat' },
]

function customRequest({ file, onFinish, onError }: UploadCustomRequestOptions) {
  // 仅占位，实际上传走 submit 按钮统一处理
  onFinish()
}

async function onSubmit() {
  const file = fileList.value[0]?.file
  if (!file) {
    message.warning('请选择账单文件')
    return
  }
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('source', form.value.source)
    if (form.value.owner_label) fd.append('owner_label', form.value.owner_label)
    fd.append('tag_ids', JSON.stringify(form.value.tag_ids))
    const task = await billApi.upload(fd)
    message.success(`已创建任务 #${task.id}，正在后台解析`)
    fileList.value = []
    form.value.owner_label = ''
    form.value.tag_ids = []
  } catch (e) {
    message.error((e as Error).message)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <n-card title="上传账单">
    <n-form label-placement="left" label-width="100" :model="form" style="max-width: 560px">
      <n-form-item label="账单来源">
        <n-select v-model:value="form.source" :options="sourceOptions" />
      </n-form-item>
      <n-form-item label="账单归属人">
        <n-input v-model:value="form.owner_label" placeholder="例如：本人 / 配偶（可选）" />
      </n-form-item>
      <n-form-item label="附加 Tag">
        <n-select
          v-model:value="form.tag_ids"
          multiple
          filterable
          :options="meta.tags.map((t) => ({ label: t.name, value: t.id }))"
          placeholder="可选"
        />
      </n-form-item>
      <n-form-item label="CSV 文件">
        <n-upload
          v-model:file-list="fileList"
          :max="1"
          :custom-request="customRequest"
          accept=".csv,text/csv"
        >
          <n-button>选择文件</n-button>
        </n-upload>
      </n-form-item>
      <n-form-item>
        <n-space>
          <n-button type="primary" :loading="submitting" @click="onSubmit">上传并解析</n-button>
          <n-button @click="$router.push('/bills/tasks')">查看任务进度</n-button>
        </n-space>
      </n-form-item>
    </n-form>
  </n-card>
</template>
