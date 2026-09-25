<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { NButton, NDatePicker, NInput, NModal, NPopconfirm, NSpace, useMessage } from 'naive-ui'
import { incomeEntryApi, type IncomeEntry, type IncomeSummary } from '@/api/finance'

const message = useMessage()
const monthTs = ref(dayjs().startOf('month').valueOf())
const month = () => dayjs(monthTs.value).format('YYYY-MM')
const year = () => dayjs(monthTs.value).year()
const entries = ref<IncomeEntry[]>([])
const summary = ref<IncomeSummary | null>(null)
const showEntry = ref(false)
const editing = ref<IncomeEntry | null>(null)
const occurredAt = ref(dayjs().format('YYYY-MM-DDTHH:mm'))
const amount = ref('')
const source = ref('')
const remark = ref('')

async function load() {
  try {
    const [rows, totals] = await Promise.all([incomeEntryApi.list({ month: month() }), incomeEntryApi.summary(year(), month())])
    entries.value = rows
    summary.value = totals
  } catch (error) { message.error((error as Error).message) }
}

function openEntry(entry?: IncomeEntry) {
  editing.value = entry || null
  const initialDate = dayjs(monthTs.value).isSame(dayjs(), 'month')
    ? dayjs() : dayjs(monthTs.value).date(1).hour(12).minute(0)
  occurredAt.value = entry ? dayjs(entry.occurred_at).format('YYYY-MM-DDTHH:mm') : initialDate.format('YYYY-MM-DDTHH:mm')
  amount.value = entry?.amount || ''
  source.value = entry?.source || ''
  remark.value = entry?.remark || ''
  showEntry.value = true
}

async function save() {
  if (!dayjs(occurredAt.value).isValid() || !/^\d+(\.\d{1,2})?$/.test(amount.value) || Number(amount.value) <= 0) {
    message.warning('请输入有效时间和正金额，最多两位小数'); return
  }
  const body = { occurred_at: occurredAt.value, amount: amount.value, source: source.value || null, remark: remark.value || null }
  try {
    if (editing.value) await incomeEntryApi.patch(editing.value.id, body)
    else await incomeEntryApi.create(body)
    showEntry.value = false
    await load()
    message.success('收入已保存')
  } catch (error) { message.error((error as Error).message) }
}

async function remove(entry: IncomeEntry) {
  try { await incomeEntryApi.remove(entry.id); await load(); message.success('已删除') }
  catch (error) { message.error((error as Error).message) }
}

watch(monthTs, load)
onMounted(load)
</script>

<template>
  <section class="finance-page">
    <div class="page-heading"><div><p class="eyebrow">INCOME</p><h1>收入</h1><p class="muted">逐笔记录实际发生时间；同月同来源可保留多笔。</p></div><n-space><n-date-picker v-model:value="monthTs" type="month" /><n-button type="primary" @click="openEntry()">记录收入</n-button></n-space></div>
    <div class="metric-grid"><div class="metric-card"><span>{{ month() }} 收入</span><strong>¥{{ summary?.month_total ?? '0.00' }}</strong><small>含旧月度记录</small></div><div class="metric-card accent"><span>{{ year() }} 年收入</span><strong>¥{{ summary?.year_total ?? '0.00' }}</strong><small>逐笔与旧月度记录合计</small></div></div>
    <div class="surface-card"><div class="card-toolbar"><h2>收入明细</h2><span class="muted">{{ month() }}</span></div><div class="table-scroller"><table class="finance-table"><thead><tr><th>发生时间</th><th>来源</th><th class="right">金额</th><th>备注</th><th>操作</th></tr></thead><tbody>
      <tr v-for="entry in entries" :key="entry.id"><td>{{ dayjs(entry.occurred_at).format('YYYY-MM-DD HH:mm') }}</td><td>{{ entry.source || '—' }}</td><td class="right strong">¥{{ entry.amount }}</td><td>{{ entry.remark || '—' }}</td><td><n-space><n-button size="small" quaternary @click="openEntry(entry)">编辑</n-button><n-popconfirm @positive-click="remove(entry)"><template #trigger><n-button size="small" quaternary>删除</n-button></template>确认删除这笔收入？</n-popconfirm></n-space></td></tr>
      <tr v-if="!entries.length"><td colspan="5" class="empty">本月暂无逐笔收入</td></tr>
    </tbody></table></div></div>
    <div v-if="summary?.legacy_monthly.length" class="surface-card"><div class="card-toolbar"><h2>旧月度记录</h2><span class="muted">旧数据没有具体发生日期，已计入月收入与年收入</span></div><div class="table-scroller"><table class="finance-table"><thead><tr><th>月份</th><th>来源</th><th class="right">金额</th><th>备注</th></tr></thead><tbody><tr v-for="entry in summary.legacy_monthly" :key="entry.id"><td>{{ entry.year_month }}</td><td>{{ entry.source }}</td><td class="right strong">¥{{ entry.amount }}</td><td>{{ entry.remark || '—' }}</td></tr></tbody></table></div></div>
    <n-modal v-model:show="showEntry" preset="card" :title="editing ? '编辑收入' : '记录收入'" style="width: min(460px, 94vw)"><div class="form-stack"><label>发生时间<input v-model="occurredAt" type="datetime-local" /></label><label>金额<n-input v-model:value="amount" placeholder="0.00" /></label><label>来源（可选）<n-input v-model:value="source" placeholder="工资 / 奖金等" /></label><label>备注（可选）<n-input v-model:value="remark" /></label></div><template #footer><n-space justify="end"><n-button @click="showEntry = false">取消</n-button><n-button type="primary" @click="save">保存</n-button></n-space></template></n-modal>
  </section>
</template>
