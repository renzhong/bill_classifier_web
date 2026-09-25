<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import dayjs from 'dayjs'
import { NButton, NDatePicker, NInput, NModal, NPagination, NSelect, NSpace, useMessage } from 'naive-ui'
import { billApi, uploadTaskApi, type Bill, type BillListQuery, type UploadTask } from '@/api/bills'
import { categoryApi, type Category } from '@/api/meta'
import { useMetaStore } from '@/stores/meta'

const route = useRoute()
const meta = useMetaStore()
const message = useMessage()
const tab = ref<'temporary' | 'archived'>('archived')
const monthTs = ref<number | null>(route.query.month ? dayjs(String(route.query.month) + '-01').valueOf() : dayjs().startOf('month').valueOf())
const filters = reactive<BillListQuery>({
  source: undefined, category_id: route.query.category_id ? Number(route.query.category_id) : undefined,
  unclassified: route.query.unclassified === '1',
  tag_id: undefined, keyword: '', page: 1, page_size: 50,
  report_expense: route.query.report_expense === '1',
})
const rows = ref<Bill[]>([])
const total = ref(0)
const loading = ref(false)
const tasks = ref<UploadTask[]>([])
const task = ref<UploadTask | null>(null)
const editingCategoryId = ref<number | null>(null)
const showUpload = ref(false)
const uploadSource = ref<'alipay' | 'wechat'>('alipay')
const uploadTags = ref<number[]>([])
const uploadFile = ref<File | null>(null)
const uploading = ref(false)
const showCategories = ref(false)
const categoryName = ref('')
const categoryEditing = ref<Category | null>(null)
let timer: ReturnType<typeof setInterval> | undefined

const categoryOptions = computed(() => meta.categories.map(c => ({ label: c.display_name || c.name, value: c.id })))
const currentRows = computed(() => rows.value)
const canWork = computed(() => task.value?.status === 'parsed' || task.value?.status === 'classified')

async function loadTasks() {
  tasks.value = (await uploadTaskApi.list()).filter(t => t.status !== 'archived')
  task.value = tasks.value.find(t => t.id === task.value?.id)
    || tasks.value.find(t => ['parsed', 'classified', 'parsing', 'pending'].includes(t.status))
    || null
}

async function loadRows() {
  loading.value = true
  try {
    if (tab.value === 'temporary' && !task.value) {
      rows.value = []
      total.value = 0
      return
    }
    const response = tab.value === 'temporary'
      ? await uploadTaskApi.bills(task.value!.id, filters.page, filters.page_size)
      : await billApi.list({ ...filters, month: monthTs.value ? dayjs(monthTs.value).format('YYYY-MM') : undefined })
    rows.value = response.items
    total.value = response.total
  } catch (error) { message.error((error as Error).message) }
  finally { loading.value = false }
}

function refresh() { filters.page = 1; void loadRows() }

function changeCategoryFilter(value: number | null) {
  filters.unclassified = value === -1
  filters.category_id = value && value > 0 ? value : undefined
  refresh()
}

async function poll() {
  if (!task.value || !['pending', 'parsing'].includes(task.value.status)) return
  try {
    task.value = await uploadTaskApi.get(task.value.id)
    if (!['pending', 'parsing'].includes(task.value.status)) {
      await loadRows()
      await loadTasks()
      if (task.value.status === 'failed') message.error(task.value.error_msg || '解析失败')
    }
  } catch (error) { message.error((error as Error).message) }
}

async function submitUpload() {
  if (!uploadFile.value) { message.warning('请选择账单文件'); return }
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', uploadFile.value)
    form.append('source', uploadSource.value)
    form.append('tag_ids', JSON.stringify(uploadTags.value))
    task.value = await billApi.upload(form)
    showUpload.value = false
    tab.value = 'temporary'
    uploadFile.value = null
    uploadTags.value = []
    await loadTasks()
    refresh()
    message.success('已上传，正在解析账单')
  } catch (error) { message.error((error as Error).message) }
  finally { uploading.value = false }
}

async function classify() {
  if (!task.value) return
  try {
    task.value = await uploadTaskApi.classify(task.value.id)
    await meta.reloadCategories()
    await loadRows()
    message.success('已运行名称正则测试规则')
  } catch (error) { message.error((error as Error).message) }
}

async function archive() {
  if (!task.value) return
  try {
    task.value = await uploadTaskApi.archive(task.value.id)
    await loadTasks()
    tab.value = 'archived'
    refresh()
    message.success('已归档，可按交易月份查询')
  } catch (error) { message.error((error as Error).message) }
}

async function selectTask(id: number | null) {
  task.value = tasks.value.find(t => t.id === id) || null
  tab.value = 'temporary'
  refresh()
}

async function changeCategory(row: Bill, event: Event) {
  const value = (event.target as HTMLSelectElement).value
  try {
    const updated = await billApi.patch(row.id, { category_id: value ? Number(value) : null })
    Object.assign(row, updated)
    editingCategoryId.value = null
    message.success('分类已保存')
  } catch (error) { message.error((error as Error).message); await loadRows() }
}

function categoryLabel(row: Bill) {
  return row.category_id === null ? '未分类' : (meta.categoryMap.get(row.category_id)?.display_name || meta.categoryMap.get(row.category_id)?.name || `#${row.category_id}`)
}

function ruleLabel(row: Bill) {
  if (row.manual_overridden) return '人工修改'
  if (row.classify_strategy_type === 'name_regex') return '名称正则 · 地铁|公交'
  return row.classify_strategy_type || '—'
}

function sourceLabel(row: Bill) {
  const platform = row.source === 'alipay' ? '支付宝' : row.source === 'wechat' ? '微信' : row.source
  const tags = row.tag_ids.map(id => meta.tagMap.get(id)?.name || `#${id}`)
  return `${platform}${tags.length ? ' · ' + tags.join(' / ') : ''}`
}

async function saveCategory() {
  if (!categoryName.value.trim()) { message.warning('请输入分类名称'); return }
  try {
    if (categoryEditing.value) await categoryApi.patch(categoryEditing.value.id, { name: categoryName.value.trim(), display_name: categoryName.value.trim() })
    else await categoryApi.create({ name: categoryName.value.trim(), display_name: null, color: null, sort_order: 0 })
    await meta.reloadCategories()
    categoryName.value = ''
    categoryEditing.value = null
    message.success('分类项已保存')
  } catch (error) { message.error((error as Error).message) }
}

async function removeCategory(id: number) {
  try {
    await categoryApi.remove(id)
    await meta.reloadCategories()
    message.success('分类项已删除')
  } catch (error) { message.error((error as Error).message) }
}

watch(tab, refresh)
watch(monthTs, () => { if (tab.value === 'archived') refresh() })
watch(() => route.query, query => {
  if (query.month) monthTs.value = dayjs(String(query.month) + '-01').valueOf()
  filters.category_id = query.category_id ? Number(query.category_id) : undefined
  filters.unclassified = query.unclassified === '1'
  filters.report_expense = query.report_expense === '1'
  tab.value = 'archived'
  refresh()
})
onMounted(async () => {
  await meta.loadAll()
  await loadTasks()
  await loadRows()
  timer = setInterval(poll, 1500)
})
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <section class="finance-page">
    <div class="page-heading">
      <div><p class="eyebrow">BILL WORKSPACE</p><h1>账单</h1><p class="muted">上传后先核对解析结果，再分类、修正并归档。</p></div>
      <n-space><n-button @click="showCategories = true">管理分类项</n-button><n-button type="primary" @click="showUpload = true">上传账单</n-button></n-space>
    </div>

    <div class="surface-card">
      <div class="tab-row">
        <button :class="{ active: tab === 'temporary' }" @click="tab = 'temporary'">临时表格</button>
        <button :class="{ active: tab === 'archived' }" @click="tab = 'archived'">归档账单</button>
      </div>
      <div v-if="tab === 'temporary'" class="card-toolbar">
        <n-space align="center" wrap>
          <n-select :value="task?.id || null" :options="tasks.map(t => ({ label: `#${t.id} · ${t.filename} · ${t.status}`, value: t.id }))" style="width: 320px" placeholder="选择上传批次" @update:value="selectTask" />
          <span class="muted">{{ task ? `状态：${task.status}，解析 ${task.total_rows} 行` : '暂无临时批次' }}</span>
        </n-space>
        <n-space><n-button :disabled="!canWork" @click="classify">开始分类</n-button><n-button type="primary" :disabled="!canWork" @click="archive">归档账单</n-button></n-space>
        <p v-if="task?.error_msg" class="muted full-width">{{ task.error_msg }}</p>
        <ul v-if="task?.parse_errors?.length" class="parse-errors full-width"><li v-for="(error, index) in task.parse_errors" :key="index">{{ error }}</li></ul>
        <p class="muted full-width">测试规则：名称正则“地铁|公交” → 交通。来源平台和上传标签不可修改。</p>
      </div>
      <div v-else class="card-toolbar">
        <p v-if="filters.report_expense" class="muted full-width">当前显示分类汇总口径：仅计入统计的支出。<button class="inline-link" @click="filters.report_expense = false; refresh()">查看全部账单</button></p>
        <n-space wrap>
          <n-date-picker v-model:value="monthTs" type="month" clearable placeholder="月份" />
          <n-select v-model:value="filters.source" :options="[{ label: '支付宝', value: 'alipay' }, { label: '微信', value: 'wechat' }]" clearable placeholder="平台" style="width: 125px" @update:value="refresh" />
          <n-select v-model:value="filters.tag_id" :options="meta.tags.map(t => ({ label: t.name, value: t.id }))" clearable placeholder="标签" style="width: 130px" @update:value="refresh" />
          <n-select :value="filters.unclassified ? -1 : filters.category_id" :options="[{ label: '未分类', value: -1 }, ...categoryOptions]" clearable placeholder="分类" style="width: 130px" @update:value="changeCategoryFilter" />
          <n-input v-model:value="filters.keyword" clearable placeholder="名称 / 商户关键词" style="width: 190px" @keyup.enter="refresh" />
          <n-button @click="refresh">查询</n-button>
        </n-space>
      </div>
      <div class="table-scroller">
        <table class="finance-table">
          <thead><tr><th>时间</th><th>名称</th><th>商户</th><th>收 / 支</th><th>来源</th><th class="right">金额</th><th>分类</th><th>分类规则</th></tr></thead>
          <tbody>
            <tr v-for="row in currentRows" :key="row.id">
              <td>{{ dayjs(row.bill_time).format('YYYY-MM-DD HH:mm') }}</td>
              <td class="strong">{{ row.item_name || '—' }}</td>
              <td>{{ row.payee || '—' }}</td>
              <td>{{ row.bill_type === 'expense' ? '支出' : row.bill_type === 'income' ? '收入' : row.bill_type }}</td>
              <td>{{ sourceLabel(row) }}</td>
              <td class="right strong">{{ row.bill_type === 'expense' ? '−' : '+' }} ¥{{ row.amount }}</td>
              <td>
                <select v-if="tab === 'temporary' || editingCategoryId === row.id" class="category-select" :value="row.category_id ?? ''" @change="changeCategory(row, $event)" @blur="editingCategoryId = null">
                  <option value="">未分类</option><option v-for="option in categoryOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
                <button v-else class="category-display" title="点击修改分类" @click="editingCategoryId = row.id">{{ categoryLabel(row) }} <span>⌄</span></button>
              </td>
              <td>{{ ruleLabel(row) }}</td>
            </tr>
            <tr v-if="!loading && !currentRows.length"><td colspan="8" class="empty">暂无账单</td></tr>
          </tbody>
        </table>
      </div>
      <div class="table-footer"><span>{{ total }} 笔账单</span><n-pagination v-model:page="filters.page" :page-size="filters.page_size" :item-count="total" @update:page="loadRows" /></div>
    </div>

    <n-modal v-model:show="showUpload" preset="card" title="上传账单" style="width: min(520px, 94vw)">
      <div class="form-stack">
        <label>账单格式<n-select v-model:value="uploadSource" :options="[{ label: '支付宝', value: 'alipay' }, { label: '微信', value: 'wechat' }]" /></label>
        <label>账单文件<input type="file" accept=".csv,.xlsx" @change="uploadFile = ($event.target as HTMLInputElement).files?.[0] || null" /></label>
        <p class="muted">支持支付宝、微信导出的 CSV / XLSX 文件。每笔交易按自身时间归入月份。</p>
        <label>添加标签（可选）<n-select v-model:value="uploadTags" multiple :options="meta.tags.map(t => ({ label: t.name, value: t.id }))" placeholder="选择账单来源标签" /></label>
      </div>
      <template #footer><n-space justify="end"><n-button @click="showUpload = false">取消</n-button><n-button type="primary" :loading="uploading" @click="submitUpload">上传并解析</n-button></n-space></template>
    </n-modal>

    <n-modal v-model:show="showCategories" preset="card" title="管理分类项" style="width: min(520px, 94vw)">
      <n-space><n-input v-model:value="categoryName" placeholder="分类名称" /><n-button type="primary" @click="saveCategory">{{ categoryEditing ? '保存' : '新增' }}</n-button></n-space>
      <div class="manage-list"><div v-for="category in meta.categories" :key="category.id" class="manage-row"><span>{{ category.display_name || category.name }}</span><n-space><n-button size="tiny" @click="categoryEditing = category; categoryName = category.name">编辑</n-button><n-button size="tiny" @click="removeCategory(category.id)">删除</n-button></n-space></div></div>
    </n-modal>
  </section>
</template>
