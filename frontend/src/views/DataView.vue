<template>
  <div style="display:flex;flex-direction:column;height:100%">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;flex-shrink:0">
      <el-date-picker v-model="period" type="month" format="YYYY-MM" value-format="YYYY-MM" @change="loadData" size="small" />
      <el-select v-model="filterItemId" placeholder="风险事项筛选" clearable filterable size="small" style="width:280px" @change="loadData">
        <el-option v-for="item in allItems" :key="item.id" :label="`${item.seq}. ${item.name}`" :value="item.id" />
      </el-select>
      <el-button type="primary" size="small" @click="exportExcel">导出Excel</el-button>
    </div>
    <el-table :data="filteredList" border style="width:100%;flex:1" height="100%" :row-style="{ height: 'auto' }">
      <el-table-column prop="seq" label="序号" width="55" fixed />
      <el-table-column prop="name" label="风险资产事项" width="200" fixed>
        <template #default="{row}">
          <div class="cell-wrap">{{ row.name }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="company" label="所属企业" width="100" />
      <el-table-column prop="amount_2025_end" label="2025年底敞口" width="80">
        <template #default="{row}">
          {{ row.amount_2025_end != null ? row.amount_2025_end.toLocaleString() : '' }}
        </template>
      </el-table-column>
      <el-table-column prop="amount_open" :label="`${periodCn}底敞口金额`" width="100">
        <template #default="{row}">
          <span v-if="row.amount_open != null" class="cell-green">{{ row.amount_open.toLocaleString() }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="amount_impairment" :label="`${periodCn}底已计提减值`" width="110">
        <template #default="{row}">
          <span v-if="row.amount_impairment != null" class="cell-green">{{ row.amount_impairment.toLocaleString() }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="amount_est_loss" label="预估损失" width="85">
        <template #default="{row}">
          <span v-if="row.amount_est_loss != null" class="cell-green">{{ row.amount_est_loss.toLocaleString() }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="xinghe_target" label="兴合集团" min-width="200">
        <template #default="{row}">
          <div class="cell-wrap">{{ row.xinghe_target || '-' }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="zhenong_target" label="浙农控股" min-width="200">
        <template #default="{row}">
          <div class="cell-wrap">{{ row.zhenong_target || '-' }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="annual_target" label="年度目标" min-width="200">
        <template #default="{row}">
          <div class="cell-wrap">{{ row.annual_target || '-' }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="leader_province" label="省社领导" width="82" />
      <el-table-column prop="leader_xinghe" label="兴合领导" width="82" />
      <el-table-column prop="leader_zhenong" label="浙农领导" width="82" />
      <el-table-column prop="leader_team" label="专班责任人" width="80">
        <template #default="{row}">
          <div class="cell-wrap">{{ row.leader_team || '-' }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="leader_dept" label="相关部门" width="82">
        <template #default="{row}">
          <div class="cell-wrap">{{ row.leader_dept || '-' }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="deadline" label="时点" width="85" />
      <el-table-column prop="target_amount" label="压降金额" width="100">
        <template #default="{row}">
          {{ row.target_amount != null ? row.target_amount.toLocaleString() : '' }}
        </template>
      </el-table-column>
      <el-table-column prop="target_ratio" label="压降比例" width="100">
        <template #default="{row}">
          {{ formatPercent(row.target_ratio) }}
        </template>
      </el-table-column>
      <el-table-column prop="progress_text" :label="`截至${periodCn}末化解进展`" min-width="240">
        <template #default="{row}">
          <div v-if="row.progress_text" class="cell-wrap cell-green" style="white-space:pre-wrap">{{ row.progress_text }}</div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import http from '../api/index'
import { ElMessage } from 'element-plus'

const period = ref('2026-05')
const dataList = ref([])
const allItems = ref([])
const filterItemId = ref(null)

const periodCn = computed(() => {
  const [y, m] = period.value.split('-')
  return `${y}年${parseInt(m)}月`
})

const filteredList = computed(() => {
  if (!filterItemId.value) return dataList.value
  return dataList.value.filter(item => item.seq === filterItemId.value)
})

function formatPercent(val) {
  if (val == null) return ''
  return (val * 100).toFixed(1) + '%'
}

async function loadData() {
  const { data } = await http.get('/api/data/detail', { params: { period: period.value } })
  dataList.value = data
  if (allItems.value.length === 0) {
    allItems.value = data.map(d => ({ id: d.seq, seq: d.seq, name: d.name }))
  }
}

function exportExcel() {
  const token = localStorage.getItem('token')
  const url = `/api/export/excel?period=${period.value}`
  fetch(url, { headers: { Authorization: `Bearer ${token}` } })
    .then(res => res.blob())
    .then(blob => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `风险资产压降进度情况表_${period.value}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    })
    .catch(() => ElMessage.error('导出失败'))
}

onMounted(loadData)
</script>

<style scoped>
.cell-wrap {
  white-space: normal;
  word-break: break-all;
  line-height: 1.5;
}
.cell-green {
  background: #92D050;
  padding: 2px 6px;
  border-radius: 2px;
  display: inline-block;
}
</style>
