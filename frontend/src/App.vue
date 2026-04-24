<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'

import { useWorkspaceStore } from './stores/workspace'

const workspace = useWorkspaceStore()
const route = useRoute()
const { failedDocumentCount, isRefreshing, lastSyncedAt, pendingDocumentCount, readyDocumentCount } = storeToRefs(workspace)

const navigation = [
  { to: '/documents', label: '文档管理', caption: 'Documents' },
  { to: '/chat', label: '聊天问答', caption: 'Chat' },
  { to: '/settings', label: '设置说明', caption: 'Settings' },
]

const pageTitle = computed(() => {
  const matched = navigation.find((item) => item.to === route.path)
  return matched?.label ?? 'RHFNJ'
})

onMounted(async () => {
  await workspace.initialize()
  workspace.startPolling()
})

onBeforeUnmount(() => {
  workspace.stopPolling()
})
</script>

<template>
  <div class="workspace-shell">
    <header class="workspace-header">
      <div>
        <p class="eyebrow">Research Workflow</p>
        <h1>RHFNJ Document Studio</h1>
        <p class="subtitle">按技术文档推进后的第四阶段界面骨架：文档、聊天、设置三块分离，并共享统一状态管理。</p>
      </div>

      <div class="header-metrics">
        <div class="metric-card">
          <span class="metric-label">已就绪</span>
          <strong>{{ readyDocumentCount }}</strong>
        </div>
        <div class="metric-card metric-card--warm">
          <span class="metric-label">处理中</span>
          <strong>{{ pendingDocumentCount }}</strong>
        </div>
        <div class="metric-card metric-card--danger">
          <span class="metric-label">失败</span>
          <strong>{{ failedDocumentCount }}</strong>
        </div>
      </div>
    </header>

    <div class="workspace-subhead">
      <span>最近同步：{{ lastSyncedAt ? new Date(lastSyncedAt).toLocaleString() : '尚未同步' }}</span>
      <el-button plain size="small" :loading="isRefreshing" @click="workspace.refreshWorkspace()">
        {{ isRefreshing ? '刷新中...' : '立即刷新工作区' }}
      </el-button>
      <div class="header-metrics header-metrics--mobile">
        <div class="metric-card">
          <span class="metric-label">已就绪</span>
          <strong>{{ readyDocumentCount }}</strong>
        </div>
        <div class="metric-card metric-card--warm">
          <span class="metric-label">处理中</span>
          <strong>{{ pendingDocumentCount }}</strong>
        </div>
        <div class="metric-card metric-card--danger">
          <span class="metric-label">失败</span>
          <strong>{{ failedDocumentCount }}</strong>
        </div>
      </div>
    </div>

    <div class="layout-shell">
      <aside class="app-nav">
        <div class="app-nav__title">
          <span>Workspace</span>
          <strong>{{ pageTitle }}</strong>
        </div>

        <nav class="app-nav__list">
          <RouterLink
            v-for="item in navigation"
            :key="item.to"
            :to="item.to"
            class="nav-link"
            active-class="nav-link--active"
          >
            <strong>{{ item.label }}</strong>
            <span>{{ item.caption }}</span>
          </RouterLink>
        </nav>
      </aside>

      <div class="route-stage">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace-shell {
  min-height: 100vh;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(245, 164, 97, 0.22), transparent 22%),
    radial-gradient(circle at top right, rgba(66, 143, 244, 0.16), transparent 20%),
    linear-gradient(180deg, #f8f1e6 0%, #f3f5f8 56%, #edf1f6 100%);
  color: #17202b;
}

.workspace-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 12px;
}

.workspace-header h1 {
  margin: 4px 0 8px;
  font-size: clamp(32px, 4vw, 48px);
  line-height: 0.98;
  letter-spacing: -0.04em;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 11px;
  color: #8f5f35;
}

.subtitle {
  max-width: 820px;
  margin: 0;
  color: #53606f;
}

.header-metrics {
  display: flex;
  gap: 12px;
}

.header-metrics--mobile {
  display: none;
}

.metric-card {
  min-width: 128px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 18px 40px rgba(51, 69, 88, 0.08);
}

.metric-card strong {
  display: block;
  margin-top: 8px;
  font-size: 28px;
  letter-spacing: -0.04em;
}

.metric-card--warm {
  background: rgba(255, 245, 233, 0.82);
}

.metric-card--danger {
  background: rgba(255, 239, 237, 0.88);
}

.metric-label {
  font-size: 12px;
  color: #5e6a78;
}

.workspace-subhead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
  padding: 0 4px;
  color: #647587;
  font-size: 13px;
}

.layout-shell {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 18px;
  min-height: calc(100vh - 180px);
}

.app-nav,
.route-stage {
  min-height: 0;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.84);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 60px rgba(33, 44, 62, 0.1);
}

.app-nav {
  padding: 18px;
}

.app-nav__title {
  margin-bottom: 18px;
}

.app-nav__title span {
  display: block;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #8f5f35;
}

.app-nav__title strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
  letter-spacing: -0.04em;
}

.app-nav__list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.nav-link {
  display: block;
  padding: 14px 15px;
  border-radius: 18px;
  text-decoration: none;
  color: inherit;
  background: #f7f9fc;
  box-shadow: inset 0 0 0 1px rgba(17, 28, 38, 0.06);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.nav-link:hover {
  transform: translateY(-1px);
}

.nav-link strong {
  display: block;
  font-size: 14px;
}

.nav-link span {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: #6c7a88;
}

.nav-link--active {
  color: #fff;
  background: linear-gradient(135deg, #17202b 0%, #25415b 100%);
  box-shadow: 0 16px 34px rgba(23, 32, 43, 0.28);
}

.nav-link--active span {
  color: rgba(255, 255, 255, 0.78);
}

.route-stage {
  padding: 18px;
}

@media (max-width: 960px) {
  .workspace-shell {
    padding: 14px;
  }

  .workspace-header {
    flex-direction: column;
    align-items: stretch;
  }

  .workspace-subhead {
    flex-direction: column;
    align-items: stretch;
  }

  .layout-shell {
    grid-template-columns: 1fr;
  }

  .header-metrics {
    display: none;
  }

  .header-metrics--mobile {
    display: flex;
    width: 100%;
  }

  .app-nav__list {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .nav-link {
    flex: 1 1 180px;
  }
}
</style>
