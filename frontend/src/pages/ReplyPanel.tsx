import React, { useState } from "react";
import { api, KnowledgeBase } from "../api";

export function ReplyPanel(props: { kb: KnowledgeBase }) {
  const [noteTitle, setNoteTitle] = useState("重生之——我在小红书做游戏");
  const [noteDesc, setNoteDesc] = useState("一句话做个小游戏？说不定下一个用ai创造奇迹的独立开发者就是你～");
  const [commentText, setCommentText] = useState("请问这种游戏可以放到WPS里面吗？");
  const [reply, setReply] = useState<any | null>(null);
  const [error, setError] = useState<string>("");

  return (
    <div>
      <h3 style={{ marginTop: 0 }}>智能回复</h3>
      <div style={{ display: "grid", gap: 10 }}>
        <input value={noteTitle} onChange={(e) => setNoteTitle(e.target.value)} style={{ padding: 8 }} placeholder="帖子标题" />
        <textarea
          value={noteDesc}
          onChange={(e) => setNoteDesc(e.target.value)}
          style={{ padding: 8, minHeight: 80 }}
          placeholder="帖子内容"
        />
        <textarea
          value={commentText}
          onChange={(e) => setCommentText(e.target.value)}
          style={{ padding: 8, minHeight: 60 }}
          placeholder="评论内容"
        />
        <button
          style={{ padding: "8px 12px", width: 140 }}
          onClick={() => {
            setError("");
            setReply(null);
            api
              .replySuggest({
                kb_id: props.kb.id,
                comment: {
                  comment_id: "demo",
                  note_id: "demo_note",
                  note_title: noteTitle,
                  note_desc: noteDesc,
                  content: commentText
                },
                top_k: 5,
                inject_sales: true
              })
              .then(setReply)
              .catch((e) => setError(String(e)));
          }}
        >
          生成回复
        </button>
      </div>

      {error ? <div style={{ marginTop: 10, color: "crimson" }}>{error}</div> : null}
      {reply ? (
        <div style={{ marginTop: 12, border: "1px solid #ddd", borderRadius: 8, padding: 10 }}>
          <div style={{ fontWeight: 600 }}>回复</div>
          <div style={{ whiteSpace: "pre-wrap", marginTop: 6 }}>{reply.reply}</div>
          <div style={{ marginTop: 10 }}>意图：{reply.intent}（{reply.intent_confidence.toFixed(2)}）</div>
          <div style={{ marginTop: 6 }}>
            潜客：{reply.lead_level} / {reply.lead_score}，信号：{reply.lead_signals?.join("、")}
          </div>
          <div style={{ marginTop: 6 }}>建议动作：{reply.next_actions?.join("；")}</div>
          <div style={{ marginTop: 6 }}>耗时：{reply.latency_ms} ms</div>
          <div style={{ marginTop: 10, fontWeight: 600 }}>引用知识</div>
          <div style={{ display: "grid", gap: 10, marginTop: 6 }}>
            {reply.used_knowledge?.map((h: any, i: number) => (
              <div key={i} style={{ border: "1px solid #eee", borderRadius: 8, padding: 8 }}>
                <div style={{ fontWeight: 600 }}>score: {h.score.toFixed(3)}</div>
                <div style={{ whiteSpace: "pre-wrap", marginTop: 6 }}>{h.content}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

