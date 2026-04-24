import { createRouter, createWebHistory } from 'vue-router'

import ChatView from '../views/ChatView.vue'
import DocumentsView from '../views/DocumentsView.vue'
import SettingsView from '../views/SettingsView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/documents',
    },
    {
      path: '/documents',
      name: 'documents',
      component: DocumentsView,
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView,
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
    },
  ],
})
