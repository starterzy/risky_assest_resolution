<template>
  <div style="height:100%;display:flex;flex-direction:column">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;flex-shrink:0">
      <el-date-picker v-model="period" type="month" format="YYYY-MM" value-format="YYYY-MM" @change="loadAll" size="small" clearable placeholder="全部月份" />
    </div>
    <el-tabs v-model="activeTab" style="flex:1;display:flex;flex-direction:column;height:0" @tab-change="loadAll">
      <el-tab-pane label="待审批" name="pending" style="height:100%">
        <el-table :data="pendingList" border style="width:100%" height="100%" :row-style="{ height: 'auto' }">
          <el-table-column prop="seq" label="序号" width="50" />
          <el-table-column prop="name" label="事项名称" min-width="150">
            <template #default="{row}"><div class="cell-wrap">{{ row.name }}</div></template>
          </el-table-column>
          <el-table-column prop="period" label="月份" width="80" />
          <el-table-column prop="amount_2025_end" label="2025年底敞口" width="100">
            <template #default="{row}">{{ row.amount_2025_end != null ? row.amount_2025_end.toLocaleString() : '' }}</template>
          </el-table-column>
          <el-table-column prop="amount_open" label="敞口金额" width="100">
            <template #default="{row}">{{ row.amount_open != null ? row.amount_open.toLocaleString() : '' }}</template>
          </el-table-column>
          <el-table-column prop="amount_impairment" label="已计提减值" width="100">
            <template #default="{row}">{{ row.amount_impairment != null ? row.amount_impairment.toLocaleString() : '' }}</template>
          </el-table-column>
          <el-table-column prop="amount_est_loss" label="预估损失" width="90">
            <template #default="{row}">{{ row.amount_est_loss != null ? row.amount_est_loss.toLocaleString() : '' }}</template>
          </el-table-column>
          <el-table-column prop="progress_text" label="化解进展" min-width="180">
            <template #default="{row}"><div class="cell-wrap">{{ row.progress_text || '' }}</div></template>
          </el-table-column>
          <el-table-column label="审批链" min-width="200">
            <template #default="{row}">
              <div style="display:flex;align-items:center;gap:3px;flex-wrap:wrap">
                <template v-for="(c, i) in row.chain" :key="c.level">
                  <span v-if="i > 0" style="color:#c0c4cc">→</span>
                  <el-tag size="small" :type="chainTagType(c.status)">{{ c.approver_name }}{{ chainMark(c.status) }}</el-tag>
                </template>
                <span v-if="!row.chain || row.chain.length === 0" style="color:#909399">无</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{row}">
              <el-button size="small" type="primary" @click="openDetail(row)">审批</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="已审批记录" name="approved" v-if="store.isAdmin() || store.role === 'group_approver'" style="height:100%">
        <el-table :data="approvedList" border style="width:100%" height="100%" :row-style="{ height: 'auto' }">
          <el-table-column prop="seq" label="序号" width="50" />
          <el-table-column prop="name" label="事项名称" min-width="150">
            <template #default="{row}"><div class="cell-wrap">{{ row.name }}</div></template>
          </el-table-column>
          <el-table-column prop="period" label="月份" width="80" />
          <el-table-column prop="amount_2025_end" label="2025年底敞口" width="100">
            <template #default="{row}">{{ row.amount_2025_end != null ? row.amount_2025_end.toLocaleString() : '' }}</template>
          </el-table-column>
          <el-table-column prop="amount_open" label="敞口金额" width="100">
            <template #default="{row}">{{ row.amount_open != null ? row.amount_open.toLocaleString() : '' }}</template>
          </el-table-column>
          <el-table-column prop="amount_impairment" label="已计提减值" width="100">
            <template #default="{row}">{{ row.amount_impairment != null ? row.amount_impairment.toLocaleString() : '' }}</template>
          </el-table-column>
          <el-table-column prop="amount_est_loss" label="预估损失" width="90">
            <template #default="{row}">{{ row.amount_est_loss != null ? row.amount_est_loss.toLocaleString() : '' }}</template>
          </el-table-column>
          <el-table-column prop="progress_text" label="化解进展" min-width="180">
            <template #default="{row}"><div class="cell-wrap">{{ row.progress_text || '' }}</div></template>
          </el-table-column>
          <el-table-column label="审批链" min-width="200">
            <template #default="{row}">
              <div style="display:flex;align-items:center;gap:3px;flex-wrap:wrap">
                <template v-for="(c, i) in row.chain" :key="c.level">
                  <span v-if="i > 0" style="color:#c0c4cc">→</span>
                  <el-tag size="small" :type="chainTagType(c.status)">{{ c.approver_name }}{{ chainMark(c.status) }}</el-tag>
                </template>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{row}">
              <el-button size="small" @click="openModify(row)">修改</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="detailVisible" :title="`${detailData.seq}. ${detailData.name}`" width="700px">
      <p style="color:#909399;margin-bottom:16px">{{ detailData.company }} | {{ detailData.period }}</p>
      <el-form :model="approveForm" label-width="160px">
        <el-form-item label="截至当月底敞口金额">
          <el-input-number v-model="approveForm.amount_open" :precision="2" :controls="false" />
        </el-form-item>
        <el-form-item label="截至当月底已计提减值">
          <el-input-number v-model="approveForm.amount_impairment" :precision="2" :controls="false" />
        </el-form-item>
        <el-form-item label="预估未体现损失">
          <el-input-number v-model="approveForm.amount_est_loss" :precision="2" :controls="false" />
        </el-form-item>
        <el-form-item label="化解进展">
          <el-input v-model="approveForm.progress_text" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="danger" @click="handleReject">驳回</el-button>
        <el-button type="primary" @click="handleApprove">通过</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="modifyVisible" :title="`修改: ${modifyData.name}`" width="700px">
      <el-form :model="modifyForm" label-width="160px">
        <el-form-item label="截至当月底敞口金额">
          <el-input-number v-model="modifyForm.amount_open" :precision="2" :controls="false" />
        </el-form-item>
        <el-form-item label="截至当月底已计提减值">
          <el-input-number v-model="modifyForm.amount_impairment" :precision="2" :controls="false" />
        </el-form-item>
        <el-form-item label="预估未体现损失">
          <el-input-number v-model="modifyForm.amount_est_loss" :precision="2" :controls="false" />
        </el-form-item>
        <el-form-item label="化解进展">
          <el-input v-model="modifyForm.progress_text" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modifyVisible = false">取消</el-button>
        <el-button type="primary" @click="handleModify">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { getPendingList, approveOrReject, getApprovedList, groupModify } from '../api/approve'
import { ElMessage } from 'element-plus'

const store = useUserStore()
const activeTab = ref('pending')
const period = ref(null)
const pendingList = ref([])
const approvedList = ref([])
const detailVisible = ref(false)
const detailData = ref({})
const approveForm = ref({})
const modifyVisible = ref(false)
const modifyData = ref({})
const modifyForm = ref({})

function chainTagType(status) {
  if (status === 'approved') return 'success'
  if (status === 'pending') return 'warning'
  if (status === 'rejected') return 'danger'
  return 'info'
}

function chainMark(status) {
  if (status === 'approved') return ' ✓'
  if (status === 'pending') return ' ⏳'
  if (status === 'rejected') return ' ✗'
  return ''
}

async function loadPending() {
  const { data } = await getPendingList(period.value || undefined)
  pendingList.value = data
}

async function loadApproved() {
  const { data } = await getApprovedList(period.value || undefined)
  approvedList.value = data
}

function loadAll() {
  loadPending()
  if (store.isAdmin() || store.role === 'group_approver') loadApproved()
}

function openDetail(row) {
  detailData.value = row
  approveForm.value = {
    amount_open: row.amount_open,
    amount_impairment: row.amount_impairment,
    amount_est_loss: row.amount_est_loss,
    progress_text: row.progress_text || '',
  }
  detailVisible.value = true
}

async function handleApprove() {
  await approveOrReject(detailData.value.record_id, { action: 'approved', ...approveForm.value })
  ElMessage.success('已通过')
  detailVisible.value = false
  await loadAll()
}

async function handleReject() {
  await approveOrReject(detailData.value.record_id, { action: 'rejected' })
  ElMessage.success('已驳回')
  detailVisible.value = false
  await loadAll()
}

function openModify(row) {
  modifyData.value = row
  modifyForm.value = {
    amount_open: row.amount_open,
    amount_impairment: row.amount_impairment,
    amount_est_loss: row.amount_est_loss,
    progress_text: row.progress_text || '',
  }
  modifyVisible.value = true
}

async function handleModify() {
  await groupModify(modifyData.value.record_id, modifyForm.value)
  ElMessage.success('已修改')
  modifyVisible.value = false
  await loadApproved()
}

onMounted(loadAll)
</script>

<style scoped>
.cell-wrap {
  white-space: normal;
  word-break: break-all;
  line-height: 1.5;
}
</style>
