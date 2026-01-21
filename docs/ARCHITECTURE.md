# 项目架构说明（前后端分离）

本项目用于“评论区智能回复 + 知识库检索 + 潜客识别 + 运营监控”。当前仓库包含：

- `backend/`：FastAPI 后端（模块化、乐高式拆分）
- `frontend/`：React + Vite 前端（调用后端 API 的简版运营面板）
- `xhs/json/`：示例数据（小红书帖子与评论 JSON）

> 约定：每个业务能力都是一个独立模块（kb/vector/reply/leads/monitor），模块对外只暴露 API（router）与内部 service，不跨模块乱引用数据库表。

---

## 后端（backend/）

### 目录结构

- `backend/app/main.py`：FastAPI 应用入口，挂载所有模块路由、CORS、启动时建表
- `backend/app/core/`：全局基础设施（配置、数据库连接）
- `backend/app/models.py`：集中导入所有 SQLModel 表，确保建表时被加载
- `backend/app/modules/`：业务模块目录（每个模块独立维护 router / service / schemas / models）
- `backend/scripts/`：端到端演示脚本（离线跑通流程）
- `backend/tests/`：轻量 smoke 测试脚本
- `backend/.env.example`：环境变量模板
- `backend/requirements.txt`：Python 依赖

---

## 后端模块拆分（每个文件负责什么）

### 1) core：配置与数据库

- `backend/app/core/config.py`
  - 读取 `.env` 环境变量
  - 提供 `settings`：数据库地址、GLM Key、模型名、向量索引目录等
- `backend/app/core/db.py`
  - 创建 SQLModel 引擎 `engine`
  - `create_db_and_tables()`：启动时建表（会 import `app.models` 确保所有表都被注册）
  - `get_session()`：FastAPI 依赖注入用的 DB Session

### 2) kb：知识库管理（多知识库、条目、修订、发布、分块）

- `backend/app/modules/kb/models.py`
  - `KnowledgeBase`：知识库（slug/name/description/published_version）
  - `KnowledgeItem`：知识条目（key/title/tags/is_active/current_revision_id）
  - `KnowledgeItemRevision`：条目修订（revision/content/status/published_version）
  - `KnowledgeChunk`：修订内容分块（用于向量化与检索）
- `backend/app/modules/kb/schemas.py`
  - API 入参/出参的 Pydantic 模型（create/update/read/publish）
- `backend/app/modules/kb/service.py`
  - 业务逻辑层（CRUD + 版本发布 + 自动分块）
  - `publish_kb()`：知识库发布版本号自增，并标记当前 revision 的 `published_version`
  - `iter_current_chunks()`：产出“当前生效的知识分块”给向量索引使用
- `backend/app/modules/kb/router.py`
  - 对外 HTTP API（/api/kbs、/api/kbs/{kb_id}/items、/publish 等）

### 3) vector：向量化与检索（Embedding 抽象、FAISS、混合检索）

- `backend/app/modules/vector/models.py`
  - `VectorIndex`：某个 kb_id + kb_version 的索引元数据（provider/model/dim/index_path）
  - `VectorRecord`：向量位置与 chunk 的映射（vector_pos -> chunk_id/revision_id）
  - `VectorQueryLog`：检索查询日志（用于监控与离线评测）
- `backend/app/modules/vector/embedding.py`
  - Embedding 客户端抽象 `EmbeddingClient`
  - `GLMEmbeddingClient`：用 GLM Embedding 接口生成向量
  - `MockHashEmbeddingClient`：无 Key 时的离线兜底向量（保证开发可跑通）
  - `get_embedding_client()`：根据环境变量自动选择实现
- `backend/app/modules/vector/faiss_store.py`
  - FAISS 向量索引封装（IndexFlatIP）
  - `save/load/search`：落盘、加载、向量检索
- `backend/app/modules/vector/service.py`
  - `reindex_kb()`：从 kb 的当前知识分块生成向量，构建并持久化 FAISS 索引
  - `search()`：向量召回 + 词面相似度（RapidFuzz）混合打分，返回 TopK
- `backend/app/modules/vector/schemas.py`
  - 重建索引与检索接口的请求/响应结构
- `backend/app/modules/vector/router.py`
  - `/api/kbs/{kb_id}/reindex`：重建索引
  - `/api/kbs/{kb_id}/search`：检索

### 4) reply：智能回复引擎（意图识别、RAG、模板兜底、合规）

- `backend/app/modules/reply/intent.py`
  - 基于规则的意图识别：buy_intent / after_sales / complaint / question / praise / chat / empty
- `backend/app/modules/reply/glm_chat.py`
  - `GLMChatClient`：调用 GLM Chat Completions（有 Key 时启用）
  - `get_chat_client()`：无 Key 返回 None
- `backend/app/modules/reply/templates.py`
  - 模板渲染与各意图的兜底话术（无 LLM 时仍可回复）
- `backend/app/modules/reply/policy.py`
  - 合规与风格：脱敏（手机号/微信/外链），长度控制
- `backend/app/modules/reply/service.py`
  - `suggest_reply()`：全链路组装
    - 意图识别
    - RAG 检索（调用 vector 模块）
    - 生成回复（GLM 或模板）
    - 合规过滤
    - 写入监控事件（monitor 模块）
- `backend/app/modules/reply/schemas.py`
  - 回复接口的入参/出参结构（包含 used_knowledge、lead、next_actions 等）
- `backend/app/modules/reply/router.py`
  - `/api/reply/suggest`：给一条评论生成一条建议回复

### 5) leads：潜客识别与运营建议

- `backend/app/modules/leads/service.py`
  - `score_lead()`：输出潜客分（0-100）、分层（low/medium/high）、触发信号与建议动作
- `backend/app/modules/leads/schemas.py`
  - 潜客评分接口请求/响应结构
- `backend/app/modules/leads/router.py`
  - `/api/leads/score`：独立的潜客评分 API（可用于 A/B 测试或前端单独调用）

### 6) monitor：运营监控（事件日志 + 聚合指标）

- `backend/app/modules/monitor/models.py`
  - `ReplyEvent`：每次生成回复的事件记录（intent、lead、latency、是否使用 LLM、时间等）
- `backend/app/modules/monitor/service.py`
  - `log_reply_event()`：写入事件
  - `overview()`：聚合指标（总量/平均延迟/LLM 占比/意图分布/潜客分层）
  - `note_top_leads()`：按 note_id 拉取 Top 潜客事件
- `backend/app/modules/monitor/schemas.py`
  - 监控接口请求/响应结构
- `backend/app/modules/monitor/router.py`
  - `/api/monitor/overview`：整体概览
  - `/api/monitor/note-top-leads`：某笔记 Top 潜客列表

---

## 后端关键请求链路（从评论到回复）

1. 前端/调用方请求：`POST /api/reply/suggest`
2. reply 模块：
   - 识别意图（intent）
   - 调用 vector 模块检索知识（search）
   - 组装 RAG prompt 并调用 GLM（或模板兜底）
   - 合规处理（脱敏、长度控制）
   - 调用 leads 模块评分（潜客分层 + 运营建议）
   - 写入 monitor 事件（ReplyEvent）
3. 返回：回复文本 + 引用知识片段 + 潜客评分 + 建议动作 + 耗时

---

## 前端（frontend/）

### 目录结构

- `frontend/index.html`：页面模板
- `frontend/src/main.tsx`：React 入口，挂载 App
- `frontend/src/App.tsx`：简版工作台（选择知识库、发布版本、重建索引、切换页面）
- `frontend/src/api.ts`：后端 API 客户端封装（fetch）
- `frontend/src/pages/ReplyPanel.tsx`：智能回复页面（输入帖子/评论，展示回复、潜客、引用知识）
- `frontend/src/pages/SearchPanel.tsx`：知识检索页面（输入 query 查看 TopK）
- `frontend/src/pages/MonitorPanel.tsx`：运营监控页面（展示 overview 聚合指标）
- `frontend/package.json`：前端依赖与脚本
- `frontend/vite.config.ts`：Vite 配置
- `frontend/tsconfig.json`：TS 配置

### 前端调用的主要 API

- 知识库：
  - `GET /api/kbs`
  - `POST /api/kbs/{kb_id}/publish`
- 索引与检索：
  - `POST /api/kbs/{kb_id}/reindex`
  - `POST /api/kbs/{kb_id}/search`
- 回复与潜客：
  - `POST /api/reply/suggest`
  - `POST /api/leads/score`
- 监控：
  - `POST /api/monitor/overview`
  - `POST /api/monitor/note-top-leads`

