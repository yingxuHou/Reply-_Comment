import React, { useState } from "react";
import { api, KnowledgeBase } from "../api";

export function SearchPanel(props: { kb: KnowledgeBase }) {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<any[]>([]);
  const [latency, setLatency] = useState<number | null>(null);
  const [error, setError] = useState<string>("");

  return (
    <div>
      <h3 style={{ marginTop: 0 }}>知识检索</h3>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入问题/关键词"
          style={{ flex: 1, padding: 8 }}
        />
        <button
          style={{ padding: "8px 12px" }}
          onClick={() => {
            setError("");
            api
              .searchKb(props.kb.id, query, 5)
              .then((res) => {
                setHits(res.hits);
                setLatency(res.latency_ms);
              })
              .catch((e) => setError(String(e)));
          }}
        >
          搜索
        </button>
      </div>
      {error ? <div style={{ marginTop: 10, color: "crimson" }}>{error}</div> : null}
      {latency != null ? <div style={{ marginTop: 10 }}>耗时：{latency} ms</div> : null}
      <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
        {hits.map((h, i) => (
          <div key={i} style={{ border: "1px solid #ddd", borderRadius: 8, padding: 10 }}>
            <div style={{ fontWeight: 600 }}>score: {h.score.toFixed(3)}</div>
            <div style={{ whiteSpace: "pre-wrap", marginTop: 6 }}>{h.content}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

