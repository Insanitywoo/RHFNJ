import axios from 'axios'

import type {
  ChatSession,
  ChatSessionDetail,
  DocumentActionResponse,
  DocumentRecord,
  DocumentsResponse,
  IndexingTask,
  UploadResponse,
} from '../types'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '')
  ?? '/api/v1'

const http = axios.create({
  baseURL: API_BASE_URL,
})

export async function listDocuments(): Promise<DocumentRecord[]> {
  const response = await http.get<DocumentsResponse>('/files')
  return response.data.documents
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await http.post<UploadResponse>('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function listDocumentTasks(documentId: number): Promise<IndexingTask[]> {
  const response = await http.get<IndexingTask[]>(`/files/${documentId}/tasks`)
  return response.data
}

export async function getDocument(documentId: number): Promise<DocumentRecord> {
  const response = await http.get<DocumentRecord>(`/files/${documentId}`)
  return response.data
}

export async function getTask(taskId: number): Promise<IndexingTask> {
  const response = await http.get<IndexingTask>(`/files/tasks/${taskId}`)
  return response.data
}

export function getDocumentDownloadUrl(documentId: number): string {
  return `${API_BASE_URL}/files/${documentId}/download`
}

export async function reindexDocument(documentId: number): Promise<DocumentActionResponse> {
  const response = await http.post<DocumentActionResponse>(`/files/${documentId}/reindex`)
  return response.data
}

export async function deleteDocument(documentId: number): Promise<DocumentActionResponse> {
  const response = await http.delete<DocumentActionResponse>(`/files/${documentId}`)
  return response.data
}

export async function listChatSessions(): Promise<ChatSession[]> {
  const response = await http.get<ChatSession[]>('/chat/sessions')
  return response.data
}

export async function getChatSession(sessionId: number): Promise<ChatSessionDetail> {
  const response = await http.get<ChatSessionDetail>(`/chat/sessions/${sessionId}`)
  return response.data
}

export async function deleteChatSession(sessionId: number): Promise<{ message: string }> {
  const response = await http.delete<{ message: string }>(`/chat/sessions/${sessionId}`)
  return response.data
}

interface StreamChatPayload {
  message: string
  source_name: string
  session_id?: number
}

interface StreamChatOptions {
  onChunk: (text: string) => void
}

export async function streamChat(
  payload: StreamChatPayload,
  options: StreamChatOptions,
): Promise<{ sessionId: number | null }> {
  const response = await fetch(`${API_BASE_URL}/stream_chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok || !response.body) {
    let detail = 'Failed to connect to server'
    try {
      const errorPayload = await response.json()
      if (typeof errorPayload?.detail === 'string') {
        detail = errorPayload.detail
      }
    } catch {
      // Keep the fallback message when the body is not JSON.
    }
    throw new Error(detail)
  }

  const sessionHeader = response.headers.get('x-session-id')
  const sessionId = sessionHeader ? Number(sessionHeader) : null
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue

      const payloadText = line.slice(6)
      if (payloadText === '[DONE]') continue

      const parsed = JSON.parse(payloadText) as { text?: string }
      if (parsed.text) {
        options.onChunk(parsed.text)
      }
    }
  }

  return { sessionId }
}

export { API_BASE_URL }
