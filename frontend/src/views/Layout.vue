<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-logo">
        <h2>🏥 中风风险预警</h2>
        <p>联邦学习·隐私保护</p>
      </div>
      <div class="sidebar-menu">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="menu-item"
          active-class="active"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </div>
    </div>

    <!-- 主区域 -->
    <div class="main-area">
      <div class="header">
        <div class="header-left">{{ currentTitle }}</div>
        <div class="header-right">
          <el-tag v-if="user?.role === 'admin'" type="danger" effect="dark" size="small">
            管理员 · 全部医院
          </el-tag>
          <el-tag v-else type="primary" effect="dark" size="small">
            医生 · {{ user?.hospital_name }}
          </el-tag>
          <span>{{ user?.username }}</span>
          <el-button type="danger" link @click="handleLogout">退出</el-button>
        </div>
      </div>
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { logout as logoutApi } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()

const user = ref(null)
onMounted(() => {
  const u = localStorage.getItem('user')
  if (u) user.value = JSON.parse(u)
})

const menuItems = [
  { path: '/dashboard', label: '仪表盘', icon: 'DataAnalysis' },
  { path: '/patients', label: '患者管理', icon: 'User' },
  { path: '/prediction', label: '风险预测', icon: 'Warning' },
  { path: '/training', label: '联邦训练', icon: 'Cpu' }
]

const currentTitle = computed(() => {
  const item = menuItems.find(m => m.path === route.path)
  return item ? item.label : '仪表盘'
})

async function handleLogout() {
  try {
    await logoutApi()
  } catch (e) {}
  localStorage.removeItem('user')
  router.push('/login')
}
</script>