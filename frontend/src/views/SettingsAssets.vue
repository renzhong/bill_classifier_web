<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import dayjs from 'dayjs'
import { NButton, NDatePicker, NInput, NModal, NSelect, NSpace, useMessage } from 'naive-ui'
import { assetItemApi, type AssetItem, type AssetMonthSummary } from '@/api/finance'

const message = useMessage()
const monthTs = ref(dayjs().startOf('month').valueOf())
const month = () => dayjs(monthTs.value).format('YYYY-MM')
const summary = ref<AssetMonthSummary | null>(null)
const amounts = reactive<Record<number, string>>({})
const showItem = ref(false)
const itemName = ref('')
const itemKind = ref<'asset' | 'liability'>('asset')
const editing = ref<AssetItem | null>(null)
const saving = ref<number | null>(null)

async function load() {
  try {
    summary.value = await assetItemApi.month(month())
    for (const row of summary.value.items) amounts[row.id] = row.amount ?? ''
  } catch (error) { message.error((error as Error).message) }
}

function openItem(item?: AssetItem) {
  editing.value = item || null
  itemName.value = item?.name || ''
  itemKind.value = item?.kind || 'asset'
  showItem.value = true
}

async function saveItem() {
  if (!itemName.value.trim()) { message.warning('请输入项目名称'); return }
  try {
    if (editing.value) await assetItemApi.patch(editing.value.id, { name: itemName.value.trim() })
    else await assetItemApi.create({ name: itemName.value.trim(), kind: itemKind.value })
    showItem.value = false
    await load()
    message.success('项目已保存')
  } catch (error) { message.error((error as Error).message) }
}

async function setActive(row: AssetItem) {
  try {
    await assetItemApi.patch(row.id, { active: !row.active })
    await load()
  } catch (error) { message.error((error as Error).message) }
}

async function saveValue(id: number) {
  const amount = amounts[id]
  if (amount === '' || !/^\d+(\.\d{1,2})?$/.test(amount)) { message.warning('请输入非负金额，最多两位小数'); return }
  saving.value = id
  try {
    await assetItemApi.value(id, month(), { amount })
    await load()
    message.success('已保存本月金额')
  } catch (error) { message.error((error as Error).message) }
  finally { saving.value = null }
}

watch(monthTs, load)
onMounted(load)
</script>

<template>
  <section class="finance-page">
    <div class="page-heading"><div><p class="eyebrow">MONTHLY ASSETS</p><h1>资产汇总</h1><p class="muted">项目沿用到每个月，金额按月独立填写。</p></div><n-space><n-date-picker v-model:value="monthTs" type="month" /><n-button type="primary" @click="openItem()">添加资产项</n-button></n-space></div>
    <div class="metric-grid">
      <div class="metric-card"><span>资产总额</span><strong>¥{{ summary?.asset_total ?? '0.00' }}</strong><small>含已录入的投资估值</small></div>
      <div class="metric-card"><span>负债总额</span><strong>¥{{ summary?.liability_total ?? '0.00' }}</strong><small>按本月填写金额</small></div>
      <div class="metric-card accent"><span>净资产</span><strong>¥{{ summary?.net_assets ?? '0.00' }}</strong><small>{{ !summary?.items.length && !summary?.investments.length ? '暂无项目' : summary?.complete ? '数据已填写' : '数据未齐，合计仅含已录入项目' }}</small></div>
    </div>
    <div class="surface-card"><div class="card-toolbar"><h2>本月资产与负债</h2><span class="muted">留空表示待填写；填写 0 表示本月确认为零</span></div>
      <div class="table-scroller"><table class="finance-table"><thead><tr><th>项目</th><th>性质</th><th>本月金额</th><th>状态</th><th>操作</th></tr></thead><tbody>
        <tr v-for="row in summary?.items || []" :key="row.id"><td class="strong">{{ row.name }} <small v-if="!row.active" class="muted">（已停用）</small></td><td>{{ row.kind === 'asset' ? '资产' : '负债' }}</td><td><n-input v-model:value="amounts[row.id]" placeholder="待填写" :disabled="!row.included_in_total" style="width: 170px" /></td><td>{{ !row.included_in_total ? '由投资估值替代' : row.amount === null ? '待填写' : '已填写' }}</td><td><n-space><n-button size="small" :disabled="!row.included_in_total" :loading="saving === row.id" @click="saveValue(row.id)">保存</n-button><n-button size="small" quaternary @click="openItem(row)">改名</n-button><n-button size="small" quaternary @click="setActive(row)">{{ row.active ? '停用' : '启用' }}</n-button></n-space></td></tr>
        <tr v-for="row in summary?.investments || []" :key="`investment-${row.id}`"><td class="strong">{{ row.name }}</td><td>投资估值</td><td>{{ row.closing_value === null ? '待填写' : `¥${row.closing_value}` }}</td><td>来自投资页</td><td><router-link to="/investments">查看投资</router-link></td></tr>
        <tr v-if="!summary?.items.length && !summary?.investments.length"><td colspan="5" class="empty">暂无资产项，先添加一个项目</td></tr>
      </tbody></table></div>
    </div>
    <n-modal v-model:show="showItem" preset="card" :title="editing ? '编辑项目' : '添加资产项'" style="width: min(440px, 94vw)"><div class="form-stack"><label>项目名称<n-input v-model:value="itemName" placeholder="例如：招商银行储蓄卡" /></label><label v-if="!editing">性质<n-select v-model:value="itemKind" :options="[{label:'资产',value:'asset'},{label:'负债',value:'liability'}]" /></label></div><template #footer><n-space justify="end"><n-button @click="showItem = false">取消</n-button><n-button type="primary" @click="saveItem">保存</n-button></n-space></template></n-modal>
  </section>
</template>
