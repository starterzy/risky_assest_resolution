<template>
  <div style="height:100%;display:flex;flex-direction:column">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;flex-shrink:0">
      <el-date-picker v-model="period" type="month" format="YYYY-MM" value-format="YYYY-MM" @change="loadItems" />
    </div>
    <el-row :gutter="16" style="flex:1;height:0">
      <el-col :span="8" style="height:100%;overflow-y:auto">
        <el-collapse v-model="expandedCompanies">
          <el-collapse-item v-for="group in groupedItems" :key="group.company" :title="group.company" :name="group.company">
            <div v-for="item in group.items" :key="item.id"
              style="padding:8px;cursor:pointer;border-radius:4px"
              :style="{ background: selectedItem?.id === item.id ? '#ecf5ff' : 'transparent' }"
              @click="selectItem(item)">
              <div>{{ item.seq }}. {{ item.name }}</div>
              <el-tag size="small" :type="statusTag(item.status)">{{ statusText(item.status) }}</el-tag>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-col>
      <el-col :span="16" v-if="selectedItem" style="height:100%;overflow-y:auto">
        <el-card>
          <h3>{{ selectedItem.seq }}. {{ selectedItem.name }}</h3>
          <p style="color:#909399">{{ selectedItem.company }} | 2025年底敞口: {{ selectedItem.amount_2025_end }}万元</p>

          <!-- Target info -->
          <el-descriptions :column="1" border style="margin-top:16px" size="small">
            <el-descriptions-item label="兴合集团目标及举措">{{ selectedItem.xinghe_target || '-' }}</el-descriptions-item>
            <el-descriptions-item label="浙农控股目标及举措">{{ selectedItem.zhenong_target || '-' }}</el-descriptions-item>
            <el-descriptions-item label="浙农控股当年度目标及举措">{{ selectedItem.annual_target || '-' }}</el-descriptions-item>
          </el-descriptions>

          <el-form :model="form" label-width="180px" style="margin-top:20px" :disabled="!canEdit">
            <el-form-item label="截至当月底敞口金额">
              <el-input-number v-model="form.amount_open" :precision="2" :controls="false" />
              <span style="margin-left:8px">万元</span>
            </el-form-item>
            <el-form-item label="截至当月底已计提减值">
              <el-input-number v-model="form.amount_impairment" :precision="2" :controls="false" />
              <span style="margin-left:8px">万元</span>
            </el-form-item>
            <el-form-item label="预估未体现损失">
              <el-input-number v-model="form.amount_est_loss" :precision="2" :controls="false" />
              <span style="margin-left:8px">万元</span>
            </el-form-item>
            <el-form-item label="化解进展">
              <el-input v-model="form.progress_text" type="textarea" :rows="6" />
            </el-form-item>
          </el-form>
          <div style="text-align:right;margin-top:16px" v-if="canEdit">
            <el-button @click="saveDraft" :loading="saving">保存草稿</el-button>
            <el-button type="primary" @click="submit" :loading="submitting">提交审批</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="16" v-else>
        <el-empty description="请选择左侧事项" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getMyFillItems, saveFillRecord, submitFillRecord } from '../api/fill'
import { ElMessage } from 'element-plus'

const period = ref('2026-05')
const items = ref([])
const selectedItem = ref(null)
const expandedCompanies = ref([])
const saving = ref(false)
const submitting = ref(false)
const form = ref({ amount_open: null, amount_impairment: null, amount_est_loss: null, progress_text: '' })

const groupedItems = computed(() => {
  const map = {}
  for (const item of items.value) {
    if (!map[item.company]) map[item.company] = { company: item.company, items: [] }
    map[item.company].items.push(item)
  }
  return Object.values(map)
})

const canEdit = computed(() => {
  if (!selectedItem.value) return false
  const s = selectedItem.value.status
  return !s || s === 'draft' || s === 'rejected'
})

function statusTag(s) {
  if (!s) return 'info'
  if (s === 'draft') return 'warning'
  if (s === 'approved') return 'success'
  if (s === 'rejected') return 'danger'
  return ''
}

function statusText(s) {
  if (!s) return '未填报'
  if (s === 'draft') return '草稿'
  if (s === 'approved') return '已审批'
  if (s === 'rejected') return '已驳回'
  if (s.startsWith('pending_level_')) return '审批中'
  return s
}

async function loadItems() {
  const { data } = await getMyFillItems(period.value)
  items.value = data
  if (data.length > 0) expandedCompanies.value = [data[0].company]
  selectedItem.value = null
}

function selectItem(item) {
  selectedItem.value = item
  form.value = {
    amount_open: item.amount_open,
    amount_impairment: item.amount_impairment,
    amount_est_loss: item.amount_est_loss,
    progress_text: item.progress_text || '',
  }
}

async function saveDraft() {
  saving.value = true
  try {
    await saveFillRecord({
      risk_item_id: selectedItem.value.id,
      period: period.value,
      ...form.value,
    })
    ElMessage.success('已保存')
    const itemId = selectedItem.value.id
    await loadItems()
    const updated = items.value.find(i => i.id === itemId)
    if (updated) selectItem(updated)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function submit() {
  submitting.value = true
  try {
    const { data: saved } = await saveFillRecord({
      risk_item_id: selectedItem.value.id,
      period: period.value,
      ...form.value,
    })
    await submitFillRecord(saved.id)
    ElMessage.success('已提交审批')
    const itemId = selectedItem.value.id
    await loadItems()
    const updated = items.value.find(i => i.id === itemId)
    if (updated) selectItem(updated)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadItems)
</script>
