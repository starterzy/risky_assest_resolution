<template>
  <el-tabs v-model="activeTab">
    <!-- Tab 1: 用户管理 -->
    <el-tab-pane label="用户管理" name="users">
      <div style="margin-bottom:12px">
        <el-button type="primary" @click="showUserDialog()">新增用户</el-button>
      </div>
      <el-table :data="users" border style="width:100%">
        <el-table-column prop="username" label="用户名" min-width="100" />
        <el-table-column prop="name" label="姓名" min-width="80" />
        <el-table-column prop="wework_userid" label="企业微信ID" width="140" />
        <el-table-column prop="role" label="角色">
          <template #default="{row}">{{ roleMap[row.role] || row.role }}</template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态">
          <template #default="{row}">
            <el-tag :type="row.is_active ? 'success' : 'danger'">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{row}">
            <el-button size="small" @click="showUserDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDisable(row)" v-if="row.is_active">禁用</el-button>
            <el-button size="small" type="success" @click="handleEnable(row)" v-else>启用</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-dialog v-model="userDialogVisible" :title="editingUser ? '编辑用户' : '新增用户'" width="400px">
        <el-form :model="userForm" label-width="80px">
          <el-form-item label="用户名" v-if="!editingUser">
            <el-input v-model="userForm.username" />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="userForm.name" />
          </el-form-item>
          <el-form-item label="密码" v-if="!editingUser">
            <el-input v-model="userForm.password" type="password" />
          </el-form-item>
          <el-form-item label="重置密码" v-if="editingUser">
            <el-input v-model="userForm.password" type="password" placeholder="留空不修改" />
          </el-form-item>
          <el-form-item label="企业微信ID">
            <el-input v-model="userForm.wework_userid" placeholder="企业微信UserId" />
          </el-form-item>
          <el-form-item label="角色">
            <el-select v-model="userForm.role">
              <el-option label="填报者" value="filler" />
              <el-option label="审批者" value="approver" />
              <el-option label="集团审核人" value="group_approver" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="userDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveUser" :loading="saving">保存</el-button>
        </template>
      </el-dialog>
    </el-tab-pane>

    <!-- Tab 2: 事项管理 -->
    <el-tab-pane label="事项管理" name="riskItems">
      <el-table :data="riskItems" border style="width:100%" max-height="600">
        <el-table-column prop="seq" label="序号" width="60" />
        <el-table-column prop="name" label="事项名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="company" label="所属企业" min-width="120" />
        <el-table-column prop="amount_2025_end" label="2025年底敞口" min-width="120" />
        <el-table-column prop="target_amount" label="压降目标" min-width="100" />
        <el-table-column label="操作" width="100">
          <template #default="{row}">
            <el-button size="small" @click="showRiskItemDialog(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-dialog v-model="riskItemDialogVisible" title="编辑事项" width="600px">
        <el-form :model="riskItemForm" label-width="140px" v-if="editingRiskItem">
          <el-form-item label="事项名称">
            <el-input v-model="riskItemForm.name" />
          </el-form-item>
          <el-form-item label="所属企业">
            <el-input v-model="riskItemForm.company" />
          </el-form-item>
          <el-form-item label="2025年底敞口金额">
            <el-input-number v-model="riskItemForm.amount_2025_end" :precision="2" :controls="false" />
          </el-form-item>
          <el-form-item label="兴合集团目标及举措">
            <el-input v-model="riskItemForm.xinghe_target" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="浙农控股目标及举措">
            <el-input v-model="riskItemForm.zhenong_target" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="年度目标及举措">
            <el-input v-model="riskItemForm.annual_target" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="省社领导">
            <el-input v-model="riskItemForm.leader_province" />
          </el-form-item>
          <el-form-item label="兴合集团领导">
            <el-input v-model="riskItemForm.leader_xinghe" />
          </el-form-item>
          <el-form-item label="浙农控股领导">
            <el-input v-model="riskItemForm.leader_zhenong" />
          </el-form-item>
          <el-form-item label="专班责任人">
            <el-input v-model="riskItemForm.leader_team" />
          </el-form-item>
          <el-form-item label="相关部门负责人">
            <el-input v-model="riskItemForm.leader_dept" />
          </el-form-item>
          <el-form-item label="时点">
            <el-input v-model="riskItemForm.deadline" />
          </el-form-item>
          <el-form-item label="压降金额">
            <el-input-number v-model="riskItemForm.target_amount" :precision="2" :controls="false" />
          </el-form-item>
          <el-form-item label="压降比例">
            <el-input-number v-model="riskItemForm.target_ratio" :precision="4" :controls="false" :step="0.01" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="riskItemDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveRiskItem" :loading="saving">保存</el-button>
        </template>
      </el-dialog>
    </el-tab-pane>

    <!-- Tab 3: 填报权限 -->
    <el-tab-pane label="填报权限" name="permissions">
      <el-row :gutter="16">
        <el-col :span="10">
          <el-table :data="riskItems" border style="width:100%" highlight-current-row @current-change="selectPermItem" max-height="500">
            <el-table-column prop="seq" label="序号" width="60" />
            <el-table-column prop="name" label="事项名称" show-overflow-tooltip />
          </el-table>
        </el-col>
        <el-col :span="14" v-if="selectedPermItem">
          <h4>{{ selectedPermItem.seq }}. {{ selectedPermItem.name }}</h4>
          <el-checkbox-group v-model="permUserIds" style="margin-top:12px">
            <div v-for="u in fillerUsers" :key="u.id" style="margin-bottom:8px">
              <el-checkbox :value="u.id">{{ u.name }} ({{ u.username }})</el-checkbox>
            </div>
          </el-checkbox-group>
          <el-button type="primary" @click="savePermissions" :loading="savingPerm" style="margin-top:16px">保存权限</el-button>
        </el-col>
      </el-row>
    </el-tab-pane>

    <!-- Tab 4: 审批链配置 -->
    <el-tab-pane label="审批链配置" name="chains">
      <el-row :gutter="16">
        <el-col :span="10">
          <el-table :data="riskItems" border style="width:100%" highlight-current-row @current-change="selectChainItem" max-height="500">
            <el-table-column prop="seq" label="序号" width="60" />
            <el-table-column prop="name" label="事项名称" show-overflow-tooltip />
          </el-table>
        </el-col>
        <el-col :span="14" v-if="selectedChainItem">
          <h4>{{ selectedChainItem.seq }}. {{ selectedChainItem.name }}</h4>
          <div style="margin-top:12px">
            <div v-for="(chain, idx) in chainLevels" :key="idx" style="display:flex;align-items:center;margin-bottom:8px;gap:8px">
              <el-tag>第{{ chain.level }}级</el-tag>
              <el-select v-model="chain.approver_id" placeholder="选择审批人" style="width:200px">
                <el-option v-for="u in approverUsers" :key="u.id" :label="u.name" :value="u.id" />
              </el-select>
              <el-tag v-if="idx === chainLevels.length - 1 && chainLevels.length > 0" type="warning">集团审核人</el-tag>
              <el-button size="small" @click="removeChainLevel(idx)" :icon="Delete" circle />
            </div>
          </div>
          <el-button @click="addChainLevel" style="margin-top:8px">添加审批级</el-button>
          <el-button type="primary" @click="saveChain" :loading="savingChain" style="margin-top:8px;margin-left:8px">保存审批链</el-button>
        </el-col>
      </el-row>
    </el-tab-pane>
  </el-tabs>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import {
  listUsers, createUser, updateUser,
  listRiskItems, updateRiskItem,
  getFillPermissions, setFillPermissions,
  getApprovalChain, setApprovalChain
} from '../api/admin'
import { ElMessage } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'

const activeTab = ref('users')
const roleMap = { admin: '管理员', filler: '填报者', approver: '审批者', group_approver: '集团审核人' }

// ==================== User Management ====================
const users = ref([])
const userDialogVisible = ref(false)
const editingUser = ref(null)
const saving = ref(false)
const userForm = ref({ username: '', name: '', password: '', role: 'filler', wework_userid: '' })

async function loadUsers() {
  const { data } = await listUsers()
  users.value = data
}

function showUserDialog(user = null) {
  editingUser.value = user
  if (user) {
    userForm.value = { name: user.name, password: '', role: user.role, wework_userid: user.wework_userid || '' }
  } else {
    userForm.value = { username: '', name: '', password: '', role: 'filler', wework_userid: '' }
  }
  userDialogVisible.value = true
}

async function saveUser() {
  saving.value = true
  try {
    if (editingUser.value) {
      const payload = { name: userForm.value.name, role: userForm.value.role, wework_userid: userForm.value.wework_userid || null }
      if (userForm.value.password) payload.password = userForm.value.password
      await updateUser(editingUser.value.id, payload)
    } else {
      await createUser(userForm.value)
    }
    ElMessage.success('保存成功')
    userDialogVisible.value = false
    await loadUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDisable(row) {
  await updateUser(row.id, { is_active: false })
  await loadUsers()
}

async function handleEnable(row) {
  await updateUser(row.id, { is_active: true })
  await loadUsers()
}

// ==================== Risk Items ====================
const riskItems = ref([])
const riskItemDialogVisible = ref(false)
const editingRiskItem = ref(null)
const riskItemForm = ref({})

async function loadRiskItems() {
  const { data } = await listRiskItems()
  riskItems.value = data
}

function showRiskItemDialog(item) {
  editingRiskItem.value = item
  riskItemForm.value = { ...item }
  riskItemDialogVisible.value = true
}

async function saveRiskItem() {
  saving.value = true
  try {
    await updateRiskItem(editingRiskItem.value.id, riskItemForm.value)
    ElMessage.success('保存成功')
    riskItemDialogVisible.value = false
    await loadRiskItems()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// ==================== Fill Permissions ====================
const selectedPermItem = ref(null)
const permUserIds = ref([])
const savingPerm = ref(false)

const fillerUsers = computed(() => users.value.filter(u => u.role === 'filler' && u.is_active))

async function selectPermItem(item) {
  selectedPermItem.value = item
  const { data } = await getFillPermissions(item.id)
  permUserIds.value = data
}

async function savePermissions() {
  savingPerm.value = true
  try {
    await setFillPermissions(selectedPermItem.value.id, permUserIds.value)
    ElMessage.success('权限已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    savingPerm.value = false
  }
}

// ==================== Approval Chains ====================
const selectedChainItem = ref(null)
const chainLevels = ref([])
const savingChain = ref(false)

const approverUsers = computed(() => users.value.filter(u => (u.role === 'approver' || u.role === 'group_approver') && u.is_active))

async function selectChainItem(item) {
  selectedChainItem.value = item
  const { data } = await getApprovalChain(item.id)
  chainLevels.value = data.map(c => ({ level: c.level, approver_id: c.approver_id }))
  // Auto-fill group_approver if only one and no chain exists
  if (chainLevels.value.length === 0) {
    const groupApprovers = users.value.filter(u => u.role === 'group_approver' && u.is_active)
    if (groupApprovers.length === 1) {
      chainLevels.value.push({ level: 1, approver_id: groupApprovers[0].id })
    }
  }
}

function addChainLevel() {
  const maxLevel = chainLevels.value.length > 0 ? Math.max(...chainLevels.value.map(c => c.level)) : 0
  chainLevels.value.push({ level: maxLevel + 1, approver_id: null })
}

function removeChainLevel(idx) {
  chainLevels.value.splice(idx, 1)
  // Re-number levels
  chainLevels.value.forEach((c, i) => c.level = i + 1)
}

async function saveChain() {
  savingChain.value = true
  try {
    const chains = chainLevels.value.map((c, i) => ({
      level: i + 1,
      approver_id: c.approver_id,
    }))
    await setApprovalChain(selectedChainItem.value.id, chains)
    ElMessage.success('审批链已保存')
    await selectChainItem(selectedChainItem.value)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    savingChain.value = false
  }
}

// ==================== Lifecycle ====================
onMounted(() => {
  loadUsers()
  loadRiskItems()
})
</script>
