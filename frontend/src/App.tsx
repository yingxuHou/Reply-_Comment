import React, { useEffect, useMemo, useState } from "react";
import { api, KnowledgeBase, UUID } from "./api";
import { MonitorPanel } from "./pages/MonitorPanel";
import { ReplyPanel } from "./pages/ReplyPanel";
import { SearchPanel } from "./pages/SearchPanel";
import { XhsPanel } from "./pages/XhsPanel";

type TabKey = "xhs" | "reply" | "search" | "monitor";

export function App() {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [kbId, setKbId] = useState<UUID | "">("");
  const [tab, setTab] = useState<TabKey>("xhs");
  const [kbLoadError, setKbLoadError] = useState<string>("");

  useEffect(() => {
    api
      .listKbs()
      .then((rows) => {
        setKbs(rows);
        if (rows.length > 0) setKbId(rows[0].id);
      })
      .catch((e) => {
        setKbs([]);
        setKbLoadError(String(e));
      });
  }, []);

  const activeKb = useMemo(() => kbs.find((k) => k.id === kbId) ?? null, [kbs, kbId]);

  return (
    <div style={{ fontFamily: "system-ui", padding: 16, maxWidth: 1100, margin: "0 auto" }}>
      <h2 style={{ margin: 0 }}>Reply Comment Agent</h2>
      {!kbs.length ? (
        <div style={{ marginTop: 12, padding: 10, border: "1px solid #f0c36d", background: "#fff7d6", borderRadius: 8 }}>
          <div style={{ fontWeight: 600 }}>后端未连接</div>
          <div style={{ marginTop: 6, whiteSpace: "pre-wrap" }}>
            {kbLoadError ? `错误：${kbLoadError}\n` : ""}
            请确认后端已启动在 http://localhost:8000，然后刷新页面；或在 frontend/.env 配置 VITE_API_BASE 指向后端 /api。
          </div>
        </div>
      ) : null}
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 12 }}>
        <label>知识库</label>
        <select value={kbId} onChange={(e) => setKbId(e.target.value)} style={{ padding: 6, minWidth: 280 }}>
          {kbs.map((k) => (
            <option key={k.id} value={k.id}>
              {k.name} ({k.slug})
            </option>
          ))}
        </select>
        <button
          disabled={!kbId}
          onClick={() => kbId && api.publishKb(kbId).then(() => api.listKbs().then(setKbs))}
          style={{ padding: "6px 10px" }}
        >
          发布版本
        </button>
        <button disabled={!kbId} onClick={() => kbId && api.reindexKb(kbId)} style={{ padding: "6px 10px" }}>
          重建索引
        </button>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button onClick={() => setTab("xhs")} style={{ padding: "6px 10px" }}>
          小红书数据
        </button>
        <button onClick={() => setTab("reply")} style={{ padding: "6px 10px" }}>
          回复引擎
        </button>
        <button onClick={() => setTab("search")} style={{ padding: "6px 10px" }}>
          知识检索
        </button>
        <button onClick={() => setTab("monitor")} style={{ padding: "6px 10px" }}>
          运营监控
        </button>
      </div>

      <div style={{ marginTop: 16 }}>
        {tab === "xhs" && <XhsPanel kb={activeKb} />}
        {tab === "reply" && activeKb && <ReplyPanel kb={activeKb} />}
        {tab === "search" && activeKb && <SearchPanel kb={activeKb} />}
        {tab === "monitor" && <MonitorPanel />}
      </div>
    </div>
  );
}
