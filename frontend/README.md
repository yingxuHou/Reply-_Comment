# Reply Comment Agent（前端）

这是一个简版运营面板，用来调用后端 API，验证知识检索、智能回复、潜客识别与监控聚合是否正常。

## 文件说明

- `index.html`：页面模板
- `src/main.tsx`：React 入口
- `src/App.tsx`：工作台（选择知识库、发布版本、重建索引、切换页面）
- `src/api.ts`：后端 API 封装（`VITE_API_BASE` 可配置）
- `src/pages/ReplyPanel.tsx`：智能回复页面
- `src/pages/SearchPanel.tsx`：知识检索页面
- `src/pages/MonitorPanel.tsx`：运营监控页面

## 启动

```bash
npm install
npm run dev
```

默认后端地址为 `http://localhost:8000/api`，如需修改：

```bash
VITE_API_BASE=http://localhost:8000/api
```

