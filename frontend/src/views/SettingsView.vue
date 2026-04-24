<script setup lang="ts">
import { API_BASE_URL } from '../lib/api'
</script>

<template>
  <section class="view-grid view-grid--settings">
    <section class="panel">
      <div class="panel-head">
        <div>
          <p class="panel-kicker">前端结构</p>
          <h2>Settings & Notes</h2>
        </div>
      </div>

      <div class="settings-grid">
        <article class="settings-card">
          <span>Router</span>
          <strong>Vue Router 已接入</strong>
          <p>当前包含文档页、聊天页、设置页，后续可以继续拆更多产品页面。</p>
        </article>

        <article class="settings-card">
          <span>State</span>
          <strong>Pinia 已接入</strong>
          <p>文档、任务、会话和聊天消息现在由统一工作区 store 管理。</p>
        </article>

        <article class="settings-card">
          <span>API Base</span>
          <strong>{{ API_BASE_URL }}</strong>
          <p>如果后端地址变化，后续可以通过 `VITE_API_BASE_URL` 配置切换。</p>
        </article>

        <article class="settings-card">
          <span>Next</span>
          <strong>当前阶段</strong>
          <p>单用户可部署 MVP 已完成，后续重点会转到引用展示、多用户和监控能力。</p>
        </article>

        <article class="settings-card">
          <span>Deploy</span>
          <strong>Docker Ready</strong>
          <p>仓库已包含 backend、worker、frontend、postgres、redis 的 Compose 部署文件。</p>
        </article>
      </div>
    </section>
  </section>
</template>
