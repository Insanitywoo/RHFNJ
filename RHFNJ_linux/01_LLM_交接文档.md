# RHFNJ 项目交接文档（给下一位 LLM）

这份文档的目标，是让接手本项目的下一位 LLM 在没有历史上下文的情况下，也能快速理解：

- 这个项目原本想做什么
- 目前已经推进到了什么阶段
- 当前代码结构和产品能力是什么
- 有哪些已经做完
- 有哪些还没做
- 继续推进时需要优先注意什么


## 1. 项目目标

RHFNJ 是一个面向论文 / PDF 文档问答的 RAG 产品。

当前产品定位是：

**单用户可部署 MVP**

系统目标包括：

- 上传 PDF
- 解析和索引 PDF
- 通过向量检索获取上下文
- 调用大模型生成基于上下文的回答
- 以流式方式在前端展示回答
- 管理文档、任务、会话和消息
- 能在 Docker Compose 下启动完整本地环境


## 2. 当前阶段判断

当前项目已经完成从“原型”到“单用户可部署 MVP”的升级，但还没有进入“正式 SaaS 完整版”。

换句话说：

- 核心业务链路已完成
- 工程结构已成型
- 部署文件已补齐
- 还可以继续做更强的产品化升级


## 3. 当前已经完成的主要能力

### 3.1 后端

- FastAPI 应用骨架
- 配置集中管理
- 路由按模块拆分
- Service 层拆分
- SQLAlchemy ORM
- Alembic 迁移
- 文档模型
- 聊天会话模型
- 聊天消息模型
- 索引任务模型
- 文档上传
- 文档详情
- 文档列表
- 文档下载 / PDF 预览
- 文档重建索引
- 文档删除
- 删除文档时删除关联聊天会话
- 会话列表
- 会话详情
- 会话删除
- 流式聊天
- 文档 ready 状态校验
- Celery 异步索引任务
- Redis broker / backend 配置

### 3.2 前端

- Vue 3 + TypeScript
- Vue Router
- Pinia
- 文档页
- 聊天页
- 设置页
- 文档筛选与搜索
- 文档状态统计
- 文档上传
- 文档重建索引
- 文档删除
- 文档预览
- 会话搜索
- 会话删除
- 工作区统一刷新
- 任务轮询
- 最近同步时间展示

### 3.3 部署

- 后端 Dockerfile
- 前端 Dockerfile
- 前端 Nginx 配置
- docker-compose.yml
- README 运行说明


## 4. 当前技术栈

### 后端

- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- Celery
- Redis
- Uvicorn

### 前端

- Vue 3
- TypeScript
- Vite
- Vue Router
- Pinia
- Element Plus
- Axios

### RAG / AI

- LangChain
- Chroma
- HuggingFace Embedding（本地）
- DeepSeek / OpenAI 兼容模型接口
- PyMuPDF

### 部署

- Docker
- Docker Compose
- Nginx
- PostgreSQL
- Redis


## 5. 当前代码结构

### 后端

- `app/main.py`
  - FastAPI 应用入口
- `app/api/routes/`
  - `documents.py`
  - `chat.py`
  - `health.py`
- `app/services/`
  - `document_service.py`
  - `chat_service.py`
  - `task_service.py`
  - `indexing_service.py`
  - `rag_service.py`
  - `llm_service.py`
  - `vector_store.py`
- `app/models/`
  - `document.py`
  - `chat.py`
  - `task.py`
- `app/db/`
  - session / base
- `app/tasks/`
  - `indexing.py`
- `alembic/`
  - 数据库迁移
- `tests/`
  - 正式测试

### 前端

- `frontend/src/App.vue`
  - 外壳导航与工作区布局
- `frontend/src/router/`
  - 路由定义
- `frontend/src/stores/workspace.ts`
  - 工作区状态中心
- `frontend/src/views/`
  - `DocumentsView.vue`
  - `ChatView.vue`
  - `SettingsView.vue`
- `frontend/src/lib/api.ts`
  - 前端 API 封装
- `frontend/src/types.ts`
  - 类型定义


## 6. 当前核心业务链路

### 6.1 文档上传链路

1. 前端上传 PDF
2. 后端保存文件
3. 创建 `Document`
4. 创建 `IndexingTask`
5. 派发 Celery 任务
6. 前端轮询任务状态
7. Worker 解析 PDF、切块、向量化、写入 Chroma
8. 文档状态变为 `ready`

### 6.2 聊天链路

1. 前端选中 ready 文档
2. 发起 `/api/v1/stream_chat`
3. 后端校验文档状态
4. 保存用户消息
5. RAG 检索相关 chunk
6. 构造 Prompt
7. 大模型流式返回
8. 保存助手消息
9. 前端展示流式回答

### 6.3 文档删除链路

1. 删除向量库中该文档的向量数据
2. 删除关联聊天会话
3. 删除数据库文档记录
4. 删除本地文件

### 6.4 文档重建索引链路

1. 清理旧向量数据
2. 重置文档状态
3. 删除旧任务
4. 新建任务
5. 重新索引


## 7. 已知重要设计点

### 7.1 当前仍然是单用户系统

目前没有用户模型、权限系统、多租户隔离。

所有设计默认围绕单用户环境。

### 7.2 当前模型调用仍然是平台统一环境变量模式

目前后端使用：

- `DEEPSEEK_API_KEY`
- `OPENAI_API_KEY`

来自 `.env` 或容器环境变量。

但用户已经明确表达了一个未来要求：

**最终产品不应依赖平台统一 API Key，而应该支持用户登录后自己选择模型并输入自己的 API Key。**

也就是说，未来方向是：

- 用户系统
- 用户模型配置
- BYOK（Bring Your Own Key）
- 前端模型选择界面

这点非常重要，后续不要忘记。

### 7.3 当前 Chroma 向量清理是按 `source_name` 做删除

在删除文档和重建索引时，向量库删除逻辑按 `source_name` 过滤。

这在当前单用户阶段是可接受的。

### 7.4 当前 Docker 文件已写好，但在原 Windows 环境中没有完成容器级联调

原因不是代码失败，而是当时 Docker daemon 在当前工具环境下不可用，无法做最终 `docker compose up` 实测。

所以：

- Compose 文件已经存在
- 语法层面已整理
- 但迁移到 Ubuntu 后应优先完成一次真正容器联调


## 8. 当前最值得优先继续做的工作

建议下一位 LLM 接手后，优先顺序如下：

### 第一优先级：完成 Ubuntu / Docker 环境联调

目标：

- 在 Ubuntu 中重新安装依赖
- 重新创建 `.env`
- 重新跑测试
- 实际启动 `docker compose up --build`
- 修正容器级问题

这是最重要的一步，因为它能把“纸面可部署”变成“实际可部署”。

### 第二优先级：确认单用户 MVP 在 Ubuntu 下真正可运行

验证：

- 上传 PDF
- 索引任务跑通
- 文档状态轮询正常
- 聊天正常
- 删除 / 重建索引正常
- 会话删除正常

### 第三优先级：开始下一轮产品升级

如果 Ubuntu + Docker 验证通过，下一轮最值得做的是：

- 引用展示卡片
- PDF 页码跳转
- 更清晰的来源展示
- 会话标题优化

### 第四优先级：开始用户系统 + BYOK 设计

这将是后续最大的产品升级方向：

- 用户登录
- 用户 API Key 存储
- 用户自选模型
- 后端动态模型路由


## 9. 当前测试状态

最近一次验证结果：

- 后端测试：`15 passed`
- 前端构建：通过

注意：这是在 Windows 开发环境下完成的验证结果。

迁移到 Ubuntu 后必须重新验证一次。


## 10. 当前迁移到 Ubuntu 时要注意的坑

### 10.1 不要复制 Windows 下的 `.venv`

必须重新创建。

### 10.2 不要复制 `frontend/node_modules`

必须重新执行 `npm install`。

### 10.3 不建议复制旧的 SQLite 与旧的 Chroma 索引文件

建议在 Ubuntu 中重新跑迁移、重新建索引。

### 10.4 如果项目目录在 `/mnt/c/...`

不建议长期这样做。

最好直接放到 Ubuntu 原生目录，例如：

```bash
~/projects/RHFNJ
```


## 11. 当前对下一位 LLM 的具体行动建议

接手后推荐按这个顺序：

1. 阅读 `技术文档.md`
2. 阅读本交接文档
3. 检查 Ubuntu 环境中的 Docker、Python、Node 是否正常
4. 重新创建 `.venv`
5. 重新安装前端依赖
6. 新建 `.env`
7. 跑 `pytest`
8. 跑前端构建
9. 跑 `docker compose up --build`
10. 逐条验证产品主链路

如果容器联调成功，再继续下一轮产品升级。


## 12. 一句话总结

当前 RHFNJ 已经完成：

**从原型到单用户可部署 MVP 的升级。**

下一位 LLM 的首要任务不是再盲目加新功能，而是：

**先在 Ubuntu 中完成环境恢复与 Docker 容器联调，再继续下一轮产品升级。**
