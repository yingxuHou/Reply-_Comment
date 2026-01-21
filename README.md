# Reply Comment Agent（前后端分离）

面向“评论区智能回复 + 知识库检索 + 潜客识别 + 运营监控”的小型全栈项目：

- 后端：FastAPI + SQLModel（SQLite）+ 向量检索（FAISS 可选，Windows 自动降级为 NumPy 索引）
- 前端：React + Vite（简版运营面板）
- 数据：仓库内置小红书（XHS）帖子/评论示例 JSON

更完整的模块边界与链路说明见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 功能概览

- 知识库（KB）：多知识库、条目/修订、发布版本、自动分块
- 检索（Vector）：Embedding 抽象、FAISS/NumPy 索引、混合检索（向量 + 词面相似度）、查询日志
- 智能回复（Reply）：意图识别、RAG 组装、GLM 生成（可选）、模板兜底、合规过滤（脱敏/长度）
- 潜客识别（Leads）：评分（0-100）、分层（low/medium/high）、信号与建议动作
- 运营监控（Monitor）：回复事件日志与聚合指标
- XHS 面板：读取 `xhs/json/search_contents_*.json` 与 `xhs/json/search_comments_*.json` 的最新文件做浏览/分析

## 快速开始（开发环境）

### 1) 后端（FastAPI）

进入后端目录：

```bash
cd backend
```

准备环境变量（可选但推荐）：

```bash
copy .env.example .env
```

安装依赖并启动：

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- 接口文档：`http://localhost:8000/docs`
- 默认数据库：`backend/data/app.db`（由 `DATABASE_URL=sqlite:///./data/app.db` 决定）
- 向量索引目录：`backend/data/vectors`（由 `VECTOR_DIR` 决定）

LLM/向量 Key 说明：

- `GLM_API_KEY` 不填也能跑：Embedding 会使用离线兜底实现，回复会走模板兜底
- 填入 `GLM_API_KEY` 后会启用 GLM Chat/Embedding（见 `backend/.env.example`）

### 2) 前端（React + Vite）

进入前端目录：

```bash
cd frontend
```

安装并启动：

```bash
npm install
npm run dev
```

默认后端地址是 `http://localhost:8000/api`，如需修改可设置：

```bash
copy .env.example .env
```

编辑 `frontend/.env`：

```bash
VITE_API_BASE=http://localhost:8000/api
```

## 主要 API

- 知识库：
  - `GET /api/kbs`
  - `POST /api/kbs/{kb_id}/publish`
  - `POST /api/kbs/{kb_id}/items`（创建条目/修订相关接口见 Swagger）
- 索引与检索：
  - `POST /api/kbs/{kb_id}/reindex`
  - `POST /api/kbs/{kb_id}/search`
- 回复与潜客：
  - `POST /api/reply/suggest`
  - `POST /api/leads/score`
- 监控：
  - `POST /api/monitor/overview`
  - `POST /api/monitor/note-top-leads`
- XHS（读取仓库内 JSON 示例）：
  - `GET /api/xhs/notes`
  - `GET /api/xhs/notes/{note_id}/comments`
  - `POST /api/xhs/notes/{note_id}/analyze`

## 示例数据（XHS）

示例数据放在：

- `xhs/json/search_contents_*.json`：帖子列表
- `xhs/json/search_comments_*.json`：评论列表

后端的 XHS 模块会自动选择目录下“最新”的一对文件（按文件名排序）。如果你替换数据，只要保持同样的命名格式即可。

## 离线脚本

- 端到端最小演示（构建默认 KB → 发布 → 重建索引 → 生成几条回复）：
  - `python backend/scripts/demo_pipeline.py`
- 数据分析与素材生成：
  - `python tools/xhs_analyze.py`：从最新 XHS JSON 生成报告到 `docs/xhs_loreal_cream_report.json`
  - `python tools/xhs_generate_replies.py`：从报告生成示例回复到 `docs/xhs_loreal_cream_replies.md`

## 测试

```bash
cd backend
python -m pytest -q
python tests/run_smoke.py
```

## 常见问题

- Windows 上没有安装 FAISS？
  - 这是预期行为：依赖里默认跳过 Windows 的 `faiss-cpu`，运行时会自动降级为 NumPy 索引（功能可用但性能更弱）。
- 需要联网/Key 才能用吗？
  - 不需要：不填 `GLM_API_KEY` 也能跑通（Embedding 与回复均有兜底实现），适合本地开发与演示。
- 为什么不要提交 `.env`？
  - `.env` 可能包含 API Key 等敏感信息；仓库提供了 `.env.example` 作为模板。
