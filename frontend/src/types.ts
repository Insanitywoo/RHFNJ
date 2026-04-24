export interface DocumentRecord {
  id: number
  filename: string
  status: string
  chunk_count: number
  last_error: string | null
  created_at: string
  updated_at: string | null
  indexed_at: string | null
}

export interface DocumentsResponse {
  documents: DocumentRecord[]
}

export interface UploadResponse {
  status: string
  filename: string
  chunks_indexed: number | null
  message: string
  document_id: number
  task_id: number
}

export interface IndexingTask {
  id: number
  document_id: number
  task_type: string
  status: string
  celery_task_id: string | null
  message: string | null
  error: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  source_name: string | null
  created_at?: string
}

export interface ChatSession {
  id: number
  title: string
  source_name: string | null
  created_at: string
  updated_at: string | null
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[]
}

export interface ChatSessionCreateResponse {
  session: ChatSession
}

export interface DocumentActionResponse {
  message: string
  document: DocumentRecord | null
  task_id: number | null
}
