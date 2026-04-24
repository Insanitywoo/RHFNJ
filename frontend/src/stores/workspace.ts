import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  deleteChatSession as deleteChatSessionRequest,
  deleteDocument as deleteDocumentRequest,
  getChatSession,
  getTask,
  listChatSessions,
  listDocumentTasks,
  listDocuments,
  reindexDocument as reindexDocumentRequest,
  streamChat,
  uploadDocument,
} from '../lib/api'
import type { ChatMessage, ChatSession, DocumentRecord, IndexingTask } from '../types'

export const useWorkspaceStore = defineStore('workspace', () => {
  const documents = ref<DocumentRecord[]>([])
  const sessions = ref<ChatSession[]>([])
  const messages = ref<ChatMessage[]>([])
  const taskMap = ref<Record<number, IndexingTask>>({})
  const selectedDocumentId = ref<number | null>(null)
  const activeSessionId = ref<number | null>(null)
  const isUploading = ref(false)
  const isStreaming = ref(false)
  const isLoadingSession = ref(false)
  const isRefreshing = ref(false)
  const lastSyncedAt = ref<string | null>(null)

  let pollTimer: ReturnType<typeof setInterval> | null = null
  let initialized = false

  const selectedDocument = computed(() =>
    documents.value.find((document) => document.id === selectedDocumentId.value) ?? null,
  )

  const selectedDocumentTask = computed(() => {
    if (!selectedDocument.value) return null
    return taskMap.value[selectedDocument.value.id] ?? null
  })

  const filteredSessions = computed(() => {
    if (!selectedDocument.value) return sessions.value
    return sessions.value.filter((session) => session.source_name === selectedDocument.value?.filename)
  })

  const readyDocumentCount = computed(() =>
    documents.value.filter((document) => document.status === 'ready').length,
  )

  const pendingDocumentCount = computed(() =>
    documents.value.filter((document) => ['queued', 'processing'].includes(document.status)).length,
  )

  const failedDocumentCount = computed(() =>
    documents.value.filter((document) => document.status === 'failed').length,
  )

  async function loadDocumentsState(options?: { preserveSelection?: boolean }) {
    const preserveSelection = options?.preserveSelection ?? true
    const nextDocuments = await listDocuments()
    documents.value = nextDocuments

    const selectedStillExists = nextDocuments.some((document) => document.id === selectedDocumentId.value)
    if (preserveSelection && selectedStillExists) {
      return
    }

    const firstReady = nextDocuments.find((document) => document.status === 'ready')
    selectedDocumentId.value = firstReady?.id ?? nextDocuments[0]?.id ?? null
  }

  async function loadSessionsState() {
    sessions.value = await listChatSessions()
  }

  async function loadLatestTasksForPendingDocuments() {
    const pendingDocuments = documents.value.filter((document) =>
      ['queued', 'processing', 'failed'].includes(document.status),
    )

    const nextTaskMap = { ...taskMap.value }

    await Promise.all(
      pendingDocuments.map(async (document) => {
        const tasks = await listDocumentTasks(document.id)
        if (tasks.length > 0) {
          nextTaskMap[document.id] = tasks[0]
        }
      }),
    )

    taskMap.value = nextTaskMap
  }

  async function refreshPendingState() {
    const pendingDocuments = documents.value.filter((document) =>
      ['queued', 'processing'].includes(document.status),
    )
    if (!pendingDocuments.length) {
      lastSyncedAt.value = new Date().toISOString()
      return
    }

    const nextTaskMap = { ...taskMap.value }

    await Promise.all(
      pendingDocuments.map(async (document) => {
        const knownTask = taskMap.value[document.id]
        if (knownTask) {
          nextTaskMap[document.id] = await getTask(knownTask.id)
        } else {
          const tasks = await listDocumentTasks(document.id)
          if (tasks.length > 0) {
            nextTaskMap[document.id] = tasks[0]
          }
        }
      }),
    )

    taskMap.value = nextTaskMap
    await loadDocumentsState()
    lastSyncedAt.value = new Date().toISOString()
  }

  async function refreshWorkspace(options?: { preserveSelection?: boolean }) {
    isRefreshing.value = true
    try {
      await loadDocumentsState({ preserveSelection: options?.preserveSelection ?? true })
      await Promise.all([loadSessionsState(), loadLatestTasksForPendingDocuments()])
      lastSyncedAt.value = new Date().toISOString()
    } finally {
      isRefreshing.value = false
    }
  }

  async function initialize() {
    if (initialized) return
    initialized = true
    await refreshWorkspace({ preserveSelection: false })
  }

  function startPolling() {
    if (pollTimer) return
    pollTimer = setInterval(() => {
      void refreshPendingState()
    }, 3000)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function resetComposerForDocument() {
    activeSessionId.value = null
    messages.value = []
  }

  function selectDocument(documentId: number | null) {
    if (documentId === selectedDocumentId.value) return
    const activeSession = sessions.value.find((session) => session.id === activeSessionId.value)
    const nextDocument = documents.value.find((document) => document.id === documentId)
    if (activeSession && activeSession.source_name && activeSession.source_name !== nextDocument?.filename) {
      resetComposerForDocument()
    }
    selectedDocumentId.value = documentId
  }

  async function openSession(sessionId: number) {
    isLoadingSession.value = true
    try {
      const session = await getChatSession(sessionId)
      activeSessionId.value = session.id
      messages.value = session.messages

      if (session.source_name) {
        const matchedDocument = documents.value.find((document) => document.filename === session.source_name)
        if (matchedDocument) {
          selectedDocumentId.value = matchedDocument.id
        }
      }
    } finally {
      isLoadingSession.value = false
    }
  }

  function startNewChat() {
    resetComposerForDocument()
  }

  async function uploadFile(file: File) {
    isUploading.value = true
    try {
      const payload = await uploadDocument(file)
      taskMap.value[payload.document_id] = await getTask(payload.task_id)
      await refreshWorkspace({ preserveSelection: false })
      selectDocument(payload.document_id)
      resetComposerForDocument()
      return payload
    } finally {
      isUploading.value = false
    }
  }

  async function reindexDocument(documentId: number) {
    const payload = await reindexDocumentRequest(documentId)
    if (payload.document && payload.task_id) {
      taskMap.value[documentId] = await getTask(payload.task_id)
      await refreshWorkspace()
      selectDocument(documentId)
      resetComposerForDocument()
    }
    return payload
  }

  async function removeDocument(documentId: number) {
    const payload = await deleteDocumentRequest(documentId)
    delete taskMap.value[documentId]

    if (selectedDocumentId.value === documentId) {
      selectedDocumentId.value = null
      resetComposerForDocument()
    }

    await refreshWorkspace({ preserveSelection: false })
    return payload
  }

  async function removeChatSession(sessionId: number) {
    const payload = await deleteChatSessionRequest(sessionId)

    if (activeSessionId.value === sessionId) {
      resetComposerForDocument()
    }

    await loadSessionsState()
    lastSyncedAt.value = new Date().toISOString()
    return payload
  }

  async function sendMessage(content: string) {
    const question = content.trim()
    if (!question || !selectedDocument.value) return

    const userMessage: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: question,
      source_name: selectedDocument.value.filename,
    }
    const assistantMessage: ChatMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      source_name: selectedDocument.value.filename,
    }

    messages.value.push(userMessage, assistantMessage)
    isStreaming.value = true

    try {
      const result = await streamChat(
        {
          message: question,
          source_name: selectedDocument.value.filename,
          session_id: activeSessionId.value ?? undefined,
        },
        {
          onChunk(text) {
            assistantMessage.content += text
          },
        },
      )

      if (result.sessionId) {
        activeSessionId.value = result.sessionId
      }
      await loadSessionsState()
      lastSyncedAt.value = new Date().toISOString()
      return result
    } finally {
      isStreaming.value = false
    }
  }

  return {
    activeSessionId,
    documents,
    failedDocumentCount,
    filteredSessions,
    initialize,
    isLoadingSession,
    isRefreshing,
    isStreaming,
    isUploading,
    lastSyncedAt,
    loadDocumentsState,
    messages,
    openSession,
    pendingDocumentCount,
    readyDocumentCount,
    refreshWorkspace,
    refreshPendingState,
    removeChatSession,
    removeDocument,
    reindexDocument,
    resetComposerForDocument,
    selectDocument,
    selectedDocument,
    selectedDocumentId,
    selectedDocumentTask,
    sendMessage,
    sessions,
    startNewChat,
    startPolling,
    stopPolling,
    taskMap,
    uploadFile,
  }
})
