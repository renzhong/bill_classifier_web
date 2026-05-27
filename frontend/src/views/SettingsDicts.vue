<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue'
import {
  NCard, NList, NListItem, NThing, NSpace, NButton, NInput, NSelect,
  NModal, NForm, NFormItem, NDataTable, NPopconfirm, NInputGroup, NText,
  useMessage, type DataTableColumns,
} from 'naive-ui'
import { dictApi, type UserDict, type DictEntry } from '@/api/meta'
import { useMetaStore } from '@/stores/meta'

const message = useMessage()
const meta = useMetaStore()
const dicts = ref<UserDict[]>([])
const activeId = ref<number | null>(null)
const entries = ref<DictEntry[]>([])

const showCreate = ref(false)
const createForm = ref({ name: '', target_field: 'any' as 'payee' | 'item_name' | 'any', remark: '' })

const showBulk = ref(false)
const bulkText = ref('')

const addingKey = ref('')
const addingCatId = ref<number | null>(null)

async function loadDicts() {
  dicts.value = await dictApi.list()
  if (!activeId.value && dicts.value.length) activeId.value = dicts.value[0].id
}

async function loadEntries() {
  if (!activeId.value) {
    entries.value = []
    return
  }
  entries.value = await dictApi.listEntries(activeId.value)
}

watch(activeId, loadEntries)

async function createDict() {
  try {
    await dictApi.create({
      name: createForm.value.name,
      target_field: createForm.value.target_field,
      remark: createForm.value.remark || null,
    })
    showCreate.value = false
    createForm.value = { name: '', target_field: 'any', remark: '' }
    await loadDicts()
    await meta.reloadDicts()
    message.success('已创建')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function removeDict(d: UserDict) {
  try {
    await dictApi.remove(d.id)
    if (activeId.value === d.id) activeId.value = null
    await loadDicts()
    await meta.reloadDicts()
    message.success('已删除')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function addEntry() {
  if (!activeId.value || !addingKey.value || addingCatId.value == null) {
    message.warning('请输入 key 并选择类别')
    return
  }
  try {
    await dictApi.addEntry(activeId.value, { key_text: addingKey.value, category_id: addingCatId.value })
    addingKey.value = ''
    await loadEntries()
    message.success('已添加')
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function removeEntry(row: DictEntry) {
  if (!activeId.value) return
  try {
    await dictApi.removeEntry(activeId.value, row.id)
    await loadEntries()
  } catch (e) {
    message.error((e as Error).message)
  }
}

async function doBulk() {
  if (!activeId.value || !bulkText.value.trim()) return
  try {
    const res = await dictApi.bulkImport(activeId.value, bulkText.value)
    message.success(`已导入 ${res.inserted} 条`)
    showBulk.value = false
    bulkText.value = ''
    await loadEntries()
  } catch (e) {
    message.error((e as Error).message)
  }
}

const entryColumns = computed<DataTableColumns<DictEntry>>(() => [
  { title: 'ID', key: 'id', width: 70 },
  { title: '关键词', key: 'key_text' },
  {
    title: '类别',
    key: 'category_id',
    render: (r) => meta.categoryMap.get(r.category_id)?.name || `#${r.category_id}`,
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row) => h(NPopconfirm, { onPositiveClick: () => removeEntry(row) }, {
      trigger: () => h(NButton, { size: 'tiny', type: 'error' }, () => '删除'),
      default: () => '确认删除？',
    }),
  },
])

onMounted(async () => {
  await meta.loadAll()
  await loadDicts()
})
</script>

<template>
  <n-space>
    <n-card title="字典列表" style="width: 320px">
      <template #header-extra>
        <n-button size="small" type="primary" @click="showCreate = true">新增字典</n-button>
      </template>
      <n-list bordered>
        <n-list-item v-for="d in dicts" :key="d.id" :style="{ cursor: 'pointer', background: activeId === d.id ? '#eef5ff' : '' }" @click="activeId = d.id">
          <n-thing>
            <template #header>{{ d.name }}</template>
            <template #header-extra>
              <n-popconfirm @positive-click="removeDict(d)">
                <template #trigger><n-button size="tiny" type="error" text>删除</n-button></template>
                确认删除字典 {{ d.name }}？
              </n-popconfirm>
            </template>
            <n-text depth="3">{{ d.target_field }} · {{ d.entry_count }} 条</n-text>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-card>

    <n-card title="条目" style="flex: 1; min-width: 600px">
      <template #header-extra>
        <n-button size="small" :disabled="!activeId" @click="showBulk = true">CSV 粘贴导入</n-button>
      </template>
      <template v-if="!activeId">
        <n-text depth="3">左侧选择一个字典</n-text>
      </template>
      <template v-else>
        <n-space vertical>
          <n-input-group>
            <n-input v-model:value="addingKey" placeholder="关键词" style="flex: 2" />
            <n-select
              v-model:value="addingCatId"
              :options="meta.categories.map((c) => ({ label: c.name, value: c.id }))"
              placeholder="选择类别"
              style="flex: 1; min-width: 160px"
            />
            <n-button type="primary" @click="addEntry">添加</n-button>
          </n-input-group>
          <n-data-table :columns="entryColumns" :data="entries" :row-key="(r: DictEntry) => r.id" />
        </n-space>
      </template>
    </n-card>
  </n-space>

  <n-modal v-model:show="showCreate" preset="card" title="新增字典" style="width: 480px">
    <n-form label-placement="left" label-width="80">
      <n-form-item label="名称">
        <n-input v-model:value="createForm.name" />
      </n-form-item>
      <n-form-item label="字段">
        <n-select
          v-model:value="createForm.target_field"
          :options="[
            { label: '任意（payee 或 item_name）', value: 'any' },
            { label: '收款方 payee', value: 'payee' },
            { label: '商品名 item_name', value: 'item_name' },
          ]"
        />
      </n-form-item>
      <n-form-item label="备注">
        <n-input v-model:value="createForm.remark" />
      </n-form-item>
    </n-form>
    <template #footer>
      <n-space justify="end">
        <n-button @click="showCreate = false">取消</n-button>
        <n-button type="primary" @click="createDict">保存</n-button>
      </n-space>
    </template>
  </n-modal>

  <n-modal v-model:show="showBulk" preset="card" title="批量粘贴 CSV" style="width: 560px">
    <n-text depth="3">每行格式：<code>key,类别名</code>。空行与 <code>#</code> 开头的注释行忽略。类别必须已存在。</n-text>
    <n-input v-model:value="bulkText" type="textarea" :rows="12" placeholder="例如：&#10;星巴克,餐饮&#10;高德打车,交通" style="margin-top: 12px" />
    <template #footer>
      <n-space justify="end">
        <n-button @click="showBulk = false">取消</n-button>
        <n-button type="primary" @click="doBulk">导入</n-button>
      </n-space>
    </template>
  </n-modal>
</template>
