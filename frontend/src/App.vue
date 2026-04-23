<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElNotification, genFileId } from 'element-plus'
import MarkdownIt from 'markdown-it'
import axios from 'axios'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
}

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
})

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isStreaming = ref(false)
const isUploading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const scrollbarRef = ref<any>(null)
const currentPdf = ref('A_Data-Driven_Reinforcement_Learning_Enabled_Battery_Fast_Charging_Optimization_Using_Real-World_Experimental_Data.pdf')
const uploadedFiles = ref<string[]>([])

const pdfUrl = (filename: string) => {
  if (filename.startsWith('http')) return filename
  return `/${filename}`
}

const scrollToBottom = async () => {
  await nextTick()
  if (scrollbarRef.value) {
    scrollbarRef.value.setScrollTop(999999)
  } else if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const handleFileUpload = async (uploadFile: any) => {
  isUploading.value = true
  
  const formData = new FormData()
  formData.append('file', uploadFile.raw)
  
  try {
    const response = await axios.post('http://127.0.0.1:8000/api/v1/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.status === 'success') {
      ElNotification({
        title: 'Success',
        message: `${response.data.filename} uploaded and indexed!`,
        type: 'success',
      })
      uploadedFiles.value.push(response.data.filename)
      currentPdf.value = response.data.filename
    }
  } catch (error: any) {
    ElNotification({
      title: 'Error',
      message: error.response?.data?.detail || 'Upload failed',
      type: 'error',
    })
  } finally {
    isUploading.value = false
  }
}

const handleExceed = (files: File[]) => {
  const file = files[0]
  ;(file as any).uid = genFileId()
  const uploadRef = document.querySelector('.upload-trigger') as any
  if (uploadRef) {
    uploadRef.clearFiles()
    uploadRef.handleStart(file)
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isStreaming.value) return

  const userMessage: Message = {
    id: Date.now(),
    role: 'user',
    content: inputMessage.value.trim()
  }
  messages.value.push(userMessage)
  inputMessage.value = ''
  isStreaming.value = true
  scrollToBottom()

  const assistantMessage: Message = {
    id: Date.now() + 1,
    role: 'assistant',
    content: ''
  }
  messages.value.push(assistantMessage)

  try {
    const response = await fetch('http://127.0.0.1:8000/api/v1/stream_chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message: userMessage.content })
    })

    if (!response.ok || !response.body) {
      throw new Error('Network response was not ok')
    }

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
        if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6)
          if (jsonStr === '[DONE]') continue
          
          try {
            const parsed = JSON.parse(jsonStr)
            const lastIndex = messages.value.length - 1
            messages.value[lastIndex].content += parsed.text
            scrollToBottom()
          } catch (e) {
            console.error('Failed to parse SSE data:', e)
          }
        }
      }
    }
  } catch (error) {
    ElMessage.error('Failed to connect to server')
    console.error(error)
    messages.value[messages.value.length - 1].content += '\n\n[Error: Failed to get response from server]'
  } finally {
    isStreaming.value = false
  }
}

onMounted(() => {
  messages.value.push({
    id: 1,
    role: 'assistant',
    content: 'Hello! I can help you understand the PDF document. Ask me anything about the content!'
  })
  uploadedFiles.value.push(currentPdf.value)
})
</script>

<template>
  <div class="h-screen flex flex-col bg-gray-50">
    <header class="h-14 bg-white border-b border-gray-200 flex items-center px-6 shadow-sm justify-between">
      <h1 class="text-xl font-semibold text-gray-800">RHFNJ - Battery Research Assistant</h1>
      
      <div class="flex items-center gap-4">
        <el-select 
          v-model="currentPdf" 
          placeholder="Select PDF"
          class="w-64"
          @change="scrollToBottom"
        >
          <el-option
            v-for="file in uploadedFiles"
            :key="file"
            :label="file"
            :value="file"
          />
        </el-select>
        
        <el-upload
          class="upload-trigger"
          :show-file-list="false"
          :auto-upload="false"
          accept=".pdf"
          :on-change="handleFileUpload"
          :on-exceed="handleExceed"
          :limit="1"
        >
          <el-button type="primary" :loading="isUploading">
            {{ isUploading ? 'Uploading...' : 'Upload PDF' }}
          </el-button>
        </el-upload>
      </div>
    </header>

    <main class="flex-1 flex overflow-hidden">
      <div class="w-[60%] border-r border-gray-200 bg-gray-100 flex flex-col">
        <div class="p-2 bg-white border-b border-gray-200 flex items-center justify-between">
          <span class="text-sm text-gray-600 font-medium">PDF Viewer</span>
          <span class="text-xs text-gray-400">{{ currentPdf }}</span>
        </div>
        <iframe 
          :src="pdfUrl(currentPdf)" 
          class="flex-1 w-full border-0"
          title="PDF Viewer"
        />
      </div>

      <div class="w-[40%] flex flex-col bg-white">
        <div class="p-3 bg-white border-b border-gray-200">
          <span class="text-sm text-gray-600 font-medium">Chat</span>
        </div>

        <el-scrollbar ref="scrollbarRef" class="flex-1 p-4">
          <div ref="messagesContainer" class="flex flex-col gap-4 min-h-full pb-4">
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="flex"
              :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="max-w-[85%] rounded-2xl px-4 py-3"
                :class="msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-br-sm' 
                  : 'bg-gray-100 text-gray-800 rounded-bl-sm'"
              >
                <div 
                  v-if="msg.role === 'assistant'" 
                  class="prose prose-sm max-w-none whitespace-pre-wrap leading-relaxed" 
                  v-html="md ? md.render(msg.content || '') : msg.content"
                ></div>
                <div v-else class="text-sm whitespace-pre-wrap">{{ msg.content }}</div>
              </div>
            </div>

            <div v-if="isStreaming" class="flex justify-start">
              <div class="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-2">
                <span class="inline-flex gap-1">
                  <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                  <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                  <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
                </span>
              </div>
            </div>
          </div>
        </el-scrollbar>

        <div class="p-4 border-t border-gray-200 bg-white">
          <div class="flex gap-2">
            <el-input
              v-model="inputMessage"
              placeholder="Ask questions about the PDF..."
              class="flex-1"
              :disabled="isStreaming"
              @keyup.enter="sendMessage"
            />
            <el-button 
              type="primary" 
              :loading="isStreaming"
              @click="sendMessage"
            >
              Send
            </el-button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
:deep(.el-input__wrapper) {
  border-radius: 9999px;
  padding-left: 16px;
  padding-right: 16px;
}

:deep(.prose) {
  font-size: 14px;
  line-height: 1.6;
}

:deep(.prose p) {
  margin: 0 0 0.5em 0;
}

:deep(.prose p:last-child) {
  margin-bottom: 0;
}

:deep(.prose h1),
:deep(.prose h2),
:deep(.prose h3) {
  font-size: 1em;
  font-weight: 600;
  margin: 0.5em 0 0.25em 0;
}

:deep(.prose ul),
:deep(.prose ol) {
  margin: 0.25em 0;
  padding-left: 1.25em;
}

:deep(.prose li) {
  margin: 0.125em 0;
}

:deep(.prose code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 0.125em 0.25em;
  border-radius: 3px;
  font-size: 0.9em;
}

:deep(.prose strong) {
  font-weight: 600;
}
</style>