import React, { useEffect, useState } from "react";
import { api } from "../api";

export function MonitorPanel() {
  const [data, setData] = useState<any | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    api
      .monitorOverview({})
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <h3 style={{ marginTop: 0 }}>运营监控（简版）</h3>
      {error ? <div style={{ marginTop: 10, color: "crimson" }}>{error}</div> : null}
      {data ? (
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 10 }}>
          <div>总回复数：{data.total_replies}</div>
          <div>平均耗时：{data.avg_latency_ms} ms</div>
          <div>LLM 使用率：{(data.llm_rate * 100).toFixed(1)}%</div>
          <div>
            潜客分层：high {data.lead_high} / medium {data.lead_medium} / low {data.lead_low}
          </div>
          <div style={{ marginTop: 8, fontWeight: 600 }}>意图分布</div>
          <pre style={{ margin: 0, marginTop: 6 }}>{JSON.stringify(data.intent_counts, null, 2)}</pre>
        </div>
      ) : (
        <div>加载中…</div>
      )}
    </div>
  );
}

