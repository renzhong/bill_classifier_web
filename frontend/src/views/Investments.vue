<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { NButton, NDatePicker, NInput, NModal, NSelect, NSpace, useMessage } from 'naive-ui'
import { assetItemApi, investmentApi, type AssetItem, type InvestmentItem, type InvestmentMonthSummary } from '@/api/finance'

const message = useMessage()
const monthTs = ref(dayjs().startOf('month').valueOf())
const month = () => dayjs(monthTs.value).format('YYYY-MM')
const summary = ref<InvestmentMonthSummary | null>(null)
const drafts = reactive<Record<number, { buys: string; sells: string; closing_value: string }>>({})
const showItem = ref(false)
const name = ref('')
const principal = ref('0.00')
const firstMonth = ref(dayjs().format('YYYY-MM'))
const editing = ref<InvestmentItem | null>(null)
const assetItems = ref<AssetItem[]>([])
const linkedAssetId = ref<number | null>(null)
const saving = ref<number | null>(null)

async function load() {
  try {
    summary.value = await investmentApi.month(month())
    for (const row of summary.value.items) drafts[row.id] = {
      buys: row.buys, sells: row.sells, closing_value: row.closing_value ?? '',
    }
  } catch (error) { message.error((error as Error).message) }
}

async function openItem(item?: InvestmentItem) {
  editing.value = item || null
  assetItems.value = (await assetItemApi.list()).filter(row => row.kind === 'asset')
  linkedAssetId.value = item?.linked_asset_item_id || null
  name.value = item?.name || ''
  principal.value = item?.initial_principal || '0.00'
  firstMonth.value = item?.first_month || month()
  showItem.value = true
}

async function saveItem() {
  if (!name.value.trim() || !/^\d+(\.\d{1,2})?$/.test(principal.value)) { message.warning('请输入名称和非负本金'); return }
  try {
    if (editing.value) await investmentApi.patch(editing.value.id, { name: name.value.trim(), initial_principal: principal.value, linked_asset_item_id: linkedAssetId.value })
    else await investmentApi.create({ name: name.value.trim(), initial_principal: principal.value, first_month: firstMonth.value, linked_asset_item_id: linkedAssetId.value })
    showItem.value = false
    await load()
    message.success('投资项已保存')
  } catch (error) { message.error((error as Error).message) }
}

async function setActive(item: InvestmentItem) {
  try { await investmentApi.patch(item.id, { active: !item.active }); await load() }
  catch (error) { message.error((error as Error).message) }
}

async function saveMonth(id: number) {
  const draft = drafts[id]
  if (!draft || ![draft.buys, draft.sells, draft.closing_value].every(v => v === '' || /^\d+(\.\d{1,2})?$/.test(v))) {
    message.warning('金额必须为非负数，最多两位小数'); return
  }
  saving.value = id
  try {
    await investmentApi.value(id, month(), {
      buys: draft.buys || '0', sells: draft.sells || '0', closing_value: draft.closing_value || null,
    })
    await load()
    message.success('本月投资记录已保存')
  } catch (error) { message.error((error as Error).message) }
  finally { saving.value = null }
}

watch(monthTs, load)
onMounted(load)
</script>

<template>
  <section class="finance-page">
    <div class="page-heading"><div><p class="eyebrow">INVESTMENTS</p><h1>投资</h1><p class="muted">按投资项记录本金、每月买卖和月末现值。</p></div><n-space><n-date-picker v-model:value="monthTs" type="month" /><n-button type="primary" @click="openItem()">添加投资项</n-button></n-space></div>
    <div class="metric-grid"><div class="metric-card"><span>本月投资现值</span><strong>¥{{ summary?.total_value ?? '0.00' }}</strong><small>自动计入资产汇总</small></div><div class="metric-card accent"><span>本月已可计算盈亏</span><strong>¥{{ summary?.total_profit ?? '0.00' }}</strong><small>{{ !summary?.items.length ? '暂无投资项' : summary.complete ? '估值与上月数据齐全' : '部分项目缺估值，合计仅含可计算项' }}</small></div></div>
    <div class="surface-card"><div class="card-toolbar"><h2>{{ month() }} 投资项</h2><span class="muted">当月盈亏 = 月末现值 − 上月末现值 − 买入 + 卖出</span></div><div class="table-scroller"><table class="finance-table"><thead><tr><th>投资项</th><th>初始本金</th><th>本月买入</th><th>本月卖出</th><th>月末现值</th><th>本月盈亏</th><th>操作</th></tr></thead><tbody>
      <tr v-for="row in summary?.items || []" :key="row.id"><td class="strong">{{ row.name }} <small v-if="!row.active" class="muted">（已停用）</small></td><td>¥{{ row.initial_principal }}</td><td><n-input v-model:value="drafts[row.id].buys" style="width: 110px" /></td><td><n-input v-model:value="drafts[row.id].sells" style="width: 110px" /></td><td><n-input v-model:value="drafts[row.id].closing_value" placeholder="待填写" style="width: 120px" /></td><td>{{ row.profit === null ? (row.missing_previous ? '缺上月估值' : '待填写') : `¥${row.profit}` }}</td><td><n-space><n-button size="small" :loading="saving === row.id" @click="saveMonth(row.id)">保存</n-button><n-button size="small" quaternary @click="openItem(row)">编辑</n-button><n-button size="small" quaternary @click="setActive(row)">{{ row.active ? '停用' : '启用' }}</n-button></n-space></td></tr>
      <tr v-if="!summary?.items.length"><td colspan="7" class="empty">本月暂无投资项</td></tr>
    </tbody></table></div></div>
    <n-modal v-model:show="showItem" preset="card" :title="editing ? '编辑投资项' : '添加投资项'" style="width: min(460px, 94vw)"><div class="form-stack"><label>名称<n-input v-model:value="name" placeholder="例如：指数基金" /></label><label>初始本金<n-input v-model:value="principal" /></label><label v-if="!editing">开始月份<input v-model="firstMonth" type="month" /></label><label>关联已有资产项（可选）<n-select v-model:value="linkedAssetId" clearable :options="assetItems.map(item => ({ label: item.name, value: item.id }))" placeholder="关联后由投资估值替代，避免重复计入" /></label><p class="muted">如果这项投资以前作为资产项录入过，选择原资产项；从投资开始月份起，月度汇总只计入投资估值。</p></div><template #footer><n-space justify="end"><n-button @click="showItem = false">取消</n-button><n-button type="primary" @click="saveItem">保存</n-button></n-space></template></n-modal>
  </section>
</template>
