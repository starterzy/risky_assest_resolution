<template>
  <el-container class="app-layout">
    <el-aside width="200px" class="app-aside">
      <div class="aside-title">风险资产压降</div>
      <el-menu :default-active="route.path" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409eff">
        <el-menu-item index="/fill">
          <el-icon><EditPen /></el-icon>
          <span>填报</span>
        </el-menu-item>
        <el-menu-item index="/approve">
          <el-icon><Check /></el-icon>
          <span>审批</span>
        </el-menu-item>
        <el-menu-item index="/data">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据查看</span>
        </el-menu-item>
        <el-menu-item v-if="store.isAdmin()" index="/admin">
          <el-icon><Setting /></el-icon>
          <span>系统管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <span style="margin-right:12px">{{ store.name }}</span>
        <el-button text @click="handleLogout">退出</el-button>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { EditPen, Check, DataAnalysis, Setting } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

function handleLogout() {
  store.logout()
  router.push('/login')
}
</script>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}
</style>

<style scoped>
.app-layout {
  height: 100vh;
}
.app-aside {
  background: #304156;
}
.aside-title {
  color: #fff;
  padding: 16px;
  font-size: 16px;
  font-weight: bold;
  text-align: center;
}
.app-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 12px;
  height: 48px;
}
.app-main {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 8px;
}
</style>
