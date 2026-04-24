<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { storeToRefs } from 'pinia'

import { getDocumentDownloadUrl } from '../lib/api'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()
const {
  documents,
  failedDocumentCount,
  isRefreshing,
  isUploading,
  lastSyncedAt,
  pendingDocumentCount,
  readyDocumentCount,
  selectedDocument,
  selectedDocumentId,
  selectedDocumentTask,
  taskMap,
} = storeToRefs(workspace)

const searchKeyword = ref('')
const statusFilter = ref<'all' | 'ready' | 'queued' | 'processing' | 'failed'>('all')

const currentPdfUrl = computed(() =>
  selectedDocument.value ? getDocumentDownloadUrl(selectedDocument.value.id) : null,
)

const filteredDocuments = computed(() =>
  documents.value.filter((document) => {
    const matchesStatus = statusFilter.value === 'all' || document.status === statusFilter.value
    const keyword = searchKeyword.value.trim().toLowerCase()
    const matchesKeyword = !keyword || document.filename.toLowerCase().includes(keyword)
    return matchesStatus && matchesKeyword
  }),
)

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    uploaded: '已上传',
    queued: '排队中',
    processing: '处理中',
    ready: '可问答',
    failed: '失败',
  }
  return labels[status] ?? status
}

function statusTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'ready') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'queued' || status === 'processing') return 'warning'
  return 'info'
}

function formatDate(value: string | null | undefined): string {
  if (!value) return '暂无'
  return new Date(value).toLocaleString()
}

function shortFilename(filename: string): string {
  return filename.length > 34 ? `${filename.slice(0, 31)}...` : filename
}

function clearFilters() {
  searchKeyword.value = ''
  statusFilter.value = 'all'
}

async function handleUploadChange(uploadFile: { raw?: File }) {
  if (!uploadFile.raw) return

  try {
    const payload = await workspace.uploadFile(uploadFile.raw)
    ElNotification({
      title: '上传成功',
      message: `${payload.filename} 已加入索引队列。`,
      type: 'success',
    })
  } catch (error: any) {
    ElNotification({
      title: '上传失败',
      message: error?.response?.data?.detail || error?.message || '上传失败，请稍后重试',
      type: 'error',
    })
  }
}

async function handleRefresh() {
  try {
    await workspace.refreshWorkspace()
    ElMessage.success('工作区数据已刷新')
  } catch (error: any) {
    ElMessage.error(error?.message || '刷新失败')
  }
}

async function handleReindex() {
  if (!selectedDocument.value) return
  try {
    await workspace.reindexDocument(selectedDocument.value.id)
    ElMessage.success('已重新加入索引队列')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '重建索引失败')
  }
}

async function handleDelete() {
  if (!selectedDocument.value) return

  await ElMessageBox.confirm(
    `确认删除 ${selectedDocument.value.filename} 吗？这会同时移除数据库记录、本地文件和对应向量索引。`,
    '删除文档',
    {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    },
  )

  try {
    await workspace.removeDocument(selectedDocument.value.id)
    ElMessage.success('文档已删除')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '删除失败')
  }
}
</script>

<template>
  <section class="view-grid">
    <aside class="panel panel--documents">
      <div class="panel-head">
        <div>
          <p class="panel-kicker">文档库</p>
          <h2>Documents</h2>
        </div>

        <div class="document-toolbar">
          <el-button plain :loading="isRefreshing" @click="handleRefresh">
            {{ isRefreshing ? '刷新中...' : '刷新' }}
          </el-button>

          <el-upload
            :show-file-list="false"
            :auto-upload="false"
            accept=".pdf"
            :on-change="handleUploadChange"
          >
            <el-button type="primary" plain :loading="isUploading">
              {{ isUploading ? '上传中...' : '上传 PDF' }}
            </el-button>
          </el-upload>
        </div>
      </div>

      <div class="panel-note">
        这里管理文档数据库记录、索引任务和 PDF 预览入口。
      </div>

      <div class="panel-controls">
        <div class="stats-strip">
          <span class="stats-chip">全部 {{ documents.length }}</span>
          <span class="stats-chip stats-chip--ok">ready {{ readyDocumentCount }}</span>
          <span class="stats-chip stats-chip--warm">pending {{ pendingDocumentCount }}</span>
          <span class="stats-chip stats-chip--danger">failed {{ failedDocumentCount }}</span>
        </div>

        <el-input
          v-model="searchKeyword"
          placeholder="按文件名搜索文档"
          clearable
        />

        <div class="filter-row">
          <el-segmented
            v-model="statusFilter"
            :options="[
              { label: '全部', value: 'all' },
              { label: 'ready', value: 'ready' },
              { label: '队列', value: 'queued' },
              { label: '处理中', value: 'processing' },
              { label: '失败', value: 'failed' },
            ]"
          />
          <el-button text @click="clearFilters">清空筛选</el-button>
        </div>

        <div class="sync-note">
          最近同步：{{ lastSyncedAt ? formatDate(lastSyncedAt) : '尚未同步' }}
        </div>
      </div>

      <el-scrollbar class="panel-scroll">
        <div v-if="filteredDocuments.length" class="document-list">
          <button
            v-for="document in filteredDocuments"
            :key="document.id"
            class="document-card"
            :class="{ 'document-card--active': document.id === selectedDocumentId }"
            @click="workspace.selectDocument(document.id)"
          >
            <div class="document-card__top">
              <strong>{{ shortFilename(document.filename) }}</strong>
              <el-tag size="small" :type="statusTagType(document.status)">
                {{ statusLabel(document.status) }}
              </el-tag>
            </div>

            <p class="document-meta">
              {{ document.chunk_count }} chunks
              <span class="dot"></span>
              {{ formatDate(document.updated_at || document.created_at) }}
            </p>

            <p v-if="taskMap[document.id]?.message" class="document-task">
              {{ taskMap[document.id]?.message }}
            </p>

            <p v-if="document.last_error" class="document-error">
              {{ document.last_error }}
            </p>
          </button>
        </div>

        <div v-else class="empty-state">
          <p>{{ documents.length ? '没有符合筛选条件的文档。' : '还没有文档。' }}</p>
          <span>{{ documents.length ? '可以调整关键词或状态筛选。' : '先上传一份 PDF，系统会自动创建索引任务。' }}</span>
        </div>
      </el-scrollbar>
    </aside>

    <section class="panel panel--details">
      <div class="panel-head">
        <div>
          <p class="panel-kicker">文档详情</p>
          <h2>{{ selectedDocument?.filename || '请选择文档' }}</h2>
        </div>

        <div v-if="selectedDocument" class="detail-actions">
          <el-button plain @click="handleReindex">重建索引</el-button>
          <el-button type="danger" plain @click="handleDelete">删除</el-button>
        </div>
      </div>

      <div v-if="selectedDocument" class="detail-body">
        <div class="detail-metrics">
          <div class="metric-card">
            <span>当前状态</span>
            <strong>{{ statusLabel(selectedDocument.status) }}</strong>
          </div>
          <div class="metric-card">
            <span>Chunk 数量</span>
            <strong>{{ selectedDocument.chunk_count }}</strong>
          </div>
          <div class="metric-card">
            <span>最近更新时间</span>
            <strong>{{ formatDate(selectedDocument.updated_at || selectedDocument.created_at) }}</strong>
          </div>
        </div>

        <div class="detail-cta-row">
          <RouterLink v-if="selectedDocument.status === 'ready'" to="/chat" class="jump-link">
            进入聊天问答
          </RouterLink>
          <span v-else class="muted-note">文档 ready 后可直接进入聊天页。</span>
        </div>

        <div v-if="selectedDocumentTask" class="task-banner">
          <div>
            <strong>最新任务：{{ statusLabel(selectedDocumentTask.status) }}</strong>
            <p>{{ selectedDocumentTask.message || '暂无额外说明' }}</p>
          </div>
          <span>{{ formatDate(selectedDocumentTask.finished_at || selectedDocumentTask.started_at || selectedDocumentTask.created_at) }}</span>
        </div>

        <div v-if="selectedDocument.last_error" class="warning-box">
          {{ selectedDocument.last_error }}
        </div>

        <div class="viewer-frame">
          <iframe
            v-if="currentPdfUrl"
            :src="currentPdfUrl"
            title="PDF Preview"
          />
        </div>
      </div>

      <div v-else class="empty-stage">
        <p>选择左侧文档后，这里会显示数据库状态和 PDF 预览。</p>
      </div>
    </section>
  </section>
</template>
