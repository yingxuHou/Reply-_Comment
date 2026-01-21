# Reply Comment Agent（后端）

## 目录结构

- app/core：配置、数据库
- app/modules/kb：知识库（多库、条目、修订、发布、分块）
- app/modules/vector：向量化与检索（Embedding 抽象、FAISS、混合检索、查询日志）
- app/modules/reply：智能回复（意图识别、RAG 组装、GLM 生成、模板兜底、合规过滤）
- app/modules/leads：潜客识别与运营建议
- app/modules/monitor：运营监控（回复事件日志、聚合指标）

更完整的架构说明见：

- `docs/ARCHITECTURE.md`

## 环境变量

复制 `.env.example` 为 `.env`，按需填写：

- DATABASE_URL：默认 sqlite
- GLM_API_KEY：本地开发请写入 `backend/.env`（不要提交到仓库）
- VECTOR_DIR：向量索引保存目录

## 启动

安装依赖：

```bash
python -m pip install -r requirements.txt
```

启动服务：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

接口文档：

- http://localhost:8000/docs

## 最小演示

```bash
python scripts/demo_pipeline.py
```
