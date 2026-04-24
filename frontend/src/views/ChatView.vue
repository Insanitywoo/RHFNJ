<script setup lang="ts">
import MarkdownIt from 'markdown-it'
import { computed, nextTick, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { storeToRefs } from 'pinia'

import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()
const { activeSessionId, filteredSessions, isLoadingSession, isStreaming, messages, selectedDocument } = storeToRefs(workspace)
const inputMessage = ref('')
const sessionKeyword = ref('')
const scrollbarRef = ref<any>(null)

const markdown = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
})

const visibleSessions = computed(() => {
  const keyword = sessionKeyword.value.trim().toLowerCase()
  if (!keyword) return filteredSessions.value
  return filteredSessions.value.filter((session) => session.title.toLowerCase().includes(keyword))
})

async function scrollToBottom() {
  await nextTick()
  scrollbarRef.value?.setScrollTop?.(999999)
}

watch(
  () => messages.value.map((message) => message.content).join('||'),
  () => {
    void scrollToBottom()
  },
)

async function handleSend() {
  const content = inputMessage.value.trim()
  if (!content || isStreaming.value) return

  if (!selectedDocument.value) {
    ElMessage.warning('请先在文档页选择一份文档')
    return
  }

  if (selectedDocument.value.status !== 'ready') {
    ElMessage.warning('当前文档尚未 ready，请等待索引完成')
    return
  }

  try {
    await workspace.sendMessage(content)
    inputMessage.value = ''
  } catch (error: any) {
    ElMessage.error(error?.message || '发送失败')
  }
}

async function handleDeleteSession(sessionId: number) {
  await ElMessageBox.confirm(
    '确认删除这条会话吗？删除后聊天记录将无法恢复。',
    '删除会话',
    {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    },
  )

  try {
    await workspace.removeChatSession(sessionId)
    ElMessage.success('会话已删除')
  } catch (error: any) {
    ElMessage.error(error?.message || '删除失败')
  }
}
</script>

<template>
  <section class="view-grid view-grid--chat">
    <aside class="panel panel--sessions">
      <div class="panel-head">
        <div>
          <p class="panel-kicker">会话历史</p>
          <h2>Chat Sessions</h2>
        </div>

        <el-button plain @click="workspace.startNewChat" :disabled="!selectedDocument">
          新对话
        </el-button>
      </div>

      <div class="panel-note">
        当前只展示已选文档下的会话历史。
      </div>

      <div class="panel-controls">
        <el-input
          v-model="sessionKeyword"
          placeholder="搜索会话标题"
          clearable
        />
      </div>

      <el-scrollbar class="panel-scroll">
        <div v-if="visibleSessions.length" class="session-list">
          <article
            v-for="session in visibleSessions"
            :key="session.id"
            class="session-item"
            :class="{ 'session-item--active': session.id === activeSessionId }"
          >
            <button class="session-item__main" @click="workspace.openSession(session.id)">
              <strong>{{ session.title }}</strong>
              <span>{{ new Date(session.updated_at || session.created_at).toLocaleString() }}</span>
            </button>
            <el-button text class="session-item__delete" @click="handleDeleteSession(session.id)">
              删除
            </el-button>
          </article>
        </div>

        <div v-else class="empty-state">
          <p>{{ filteredSessions.length ? '没有匹配的会话' : '暂无历史会话' }}</p>
          <span>{{ filteredSessions.length ? '试试换个关键词。' : '选择 ready 文档后，可以从这里持续查看对话历史。' }}</span>
        </div>
      </el-scrollbar>
    </aside>

    <section class="panel panel--conversation">
      <div class="panel-head">
        <div>
          <p class="panel-kicker">当前对话</p>
          <h2>{{ selectedDocument?.filename || '请先选择文档' }}</h2>
        </div>
      </div>

      <div
        class="conversation-hint"
        :class="{ 'conversation-hint--warn': selectedDocument && selectedDocument.status !== 'ready' }"
      >
        <template v-if="selectedDocument">
          当前文档状态：<strong>{{ selectedDocument.status }}</strong>
          <span>{{ selectedDocument.status === 'ready' ? '可以开始问答' : '文档还未完成索引，聊天输入已限制' }}</span>
        </template>
        <template v-else>
          请先去文档页选择一份文档。
        </template>
      </div>

      <div class="chat-action-row">
        <RouterLink to="/documents" class="jump-link jump-link--ghost">
          回到文档页
        </RouterLink>
        <span class="muted-note">
          当前会话数：{{ filteredSessions.length }}
        </span>
      </div>

      <el-scrollbar ref="scrollbarRef" class="panel-scroll">
        <div v-if="messages.length" class="message-list">
          <article
            v-for="message in messages"
            :key="message.id"
            class="message-card"
            :class="message.role === 'user' ? 'message-card--user' : 'message-card--assistant'"
          >
            <header>
              <span>{{ message.role === 'user' ? 'You' : 'Assistant' }}</span>
              <small>{{ message.source_name || 'All documents' }}</small>
            </header>

            <div
              v-if="message.role === 'assistant'"
              class="message-markdown"
              v-html="markdown.render(message.content || '')"
            ></div>
            <p v-else>{{ message.content }}</p>
          </article>
        </div>

        <div v-else-if="isLoadingSession" class="empty-state">
          <p>正在加载会话...</p>
        </div>

        <div v-else class="empty-state">
          <p>从这里开始一段围绕当前文档的对话。</p>
          <span>聊天内容会自动落库，并进入会话历史。</span>
        </div>
      </el-scrollbar>

      <div class="composer">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="4"
          resize="none"
          placeholder="询问摘要、实验设置、结论依据或页码来源..."
          :disabled="isStreaming || !selectedDocument || selectedDocument.status !== 'ready'"
          @keyup.ctrl.enter="handleSend"
        />
        <div class="composer-foot">
          <span>Ctrl + Enter 发送</span>
          <el-button type="primary" :loading="isStreaming" @click="handleSend">
            {{ isStreaming ? '生成中...' : '发送' }}
          </el-button>
        </div>
      </div>
    </section>
  </section>
</template>
