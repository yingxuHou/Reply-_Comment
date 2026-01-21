import React, { useEffect, useMemo, useState } from "react";
import { api, KnowledgeBase, ReplyResponse, XhsAnalyzeResponse, XhsComment, XhsListCommentsResponse, XhsNote } from "../api";

function formatTs(ms: number | null) {
  if (!ms) return "";
  const d = new Date(ms);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(
    d.getHours()
  ).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function clampText(s: string, n: number) {
  const t = (s ?? "").trim();
  if (t.length <= n) return t;
  return t.slice(0, n) + "…";
}

function formatCount(s: string) {
  return (s ?? "").toString();
}

export function XhsPanel(props: { kb: KnowledgeBase | null }) {
  const [noteQuery, setNoteQuery] = useState("");
  const [notes, setNotes] = useState<XhsNote[]>([]);
  const [notesError, setNotesError] = useState("");
  const [activeNoteId, setActiveNoteId] = useState<string>("");

  const [sort, setSort] = useState<"like" | "time">("like");
  const [commentQuery, setCommentQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(50);
  const [commentsResp, setCommentsResp] = useState<XhsListCommentsResponse | null>(null);
  const [commentsError, setCommentsError] = useState("");
  const [analyze, setAnalyze] = useState<XhsAnalyzeResponse | null>(null);
  const [analyzeError, setAnalyzeError] = useState("");

  const [replyByCommentId, setReplyByCommentId] = useState<Record<string, ReplyResponse>>({});
  const [replyErrByCommentId, setReplyErrByCommentId] = useState<Record<string, string>>({});
  const [bulkBusy, setBulkBusy] = useState(false);
  const [bulkProgress, setBulkProgress] = useState<{ done: number; total: number }>({ done: 0, total: 0 });

  const activeNote = useMemo(() => notes.find((n) => n.note_id === activeNoteId) ?? null, [notes, activeNoteId]);

  useEffect(() => {
    api
      .xhsListNotes(noteQuery)
      .then((r) => {
        setNotes(r.notes);
        setNotesError("");
        if (!activeNoteId && r.notes.length > 0) setActiveNoteId(r.notes[0].note_id);
      })
      .catch((e) => {
        setNotes([]);
        setNotesError(String(e));
      });
  }, [noteQuery]);

  useEffect(() => {
    if (!activeNoteId) return;
    setAnalyze(null);
    setAnalyzeError("");
    api
      .xhsAnalyze(activeNoteId, 500)
      .then(setAnalyze)
      .catch((e) => setAnalyzeError(String(e)));
  }, [activeNoteId]);

  useEffect(() => {
    if (!activeNoteId) return;
    setCommentsResp(null);
    setCommentsError("");
    api
      .xhsListComments(activeNoteId, { offset, limit, sort, q: commentQuery })
      .then(setCommentsResp)
      .catch((e) => setCommentsError(String(e)));
  }, [activeNoteId, offset, limit, sort, commentQuery]);

  async function suggestForComment(c: XhsComment) {
    if (!props.kb) {
      setReplyErrByCommentId((m) => ({ ...m, [c.comment_id]: "请先选择知识库（顶部下拉框）" }));
      return;
    }
    setReplyErrByCommentId((m) => ({ ...m, [c.comment_id]: "" }));
    const payload = {
      kb_id: props.kb.id,
      comment: {
        comment_id: c.comment_id,
        note_id: c.note_id,
        note_title: activeNote?.title ?? "",
        note_desc: activeNote?.desc ?? "",
        nickname: c.nickname ?? "",
        content: c.content ?? ""
      },
      top_k: 5,
      inject_sales: true
    };
    try {
      const r = await api.replySuggest(payload);
      setReplyByCommentId((m) => ({ ...m, [c.comment_id]: r }));
    } catch (e: any) {
      setReplyErrByCommentId((m) => ({ ...m, [c.comment_id]: String(e) }));
    }
  }

  async function bulkSuggest() {
    const rows = commentsResp?.comments ?? [];
    if (!rows.length) return;
    setBulkBusy(true);
    setBulkProgress({ done: 0, total: rows.length });
    try {
      for (let i = 0; i < rows.length; i++) {
        await suggestForComment(rows[i]);
        setBulkProgress({ done: i + 1, total: rows.length });
      }
    } finally {
      setBulkBusy(false);
    }
  }

  const intentPairs = useMemo(() => {
    const m = analyze?.intent_counts ?? {};
    const arr = Object.entries(m).sort((a, b) => b[1] - a[1]);
    return arr;
  }, [analyze]);

  return (
    <div>
      <h3 style={{ marginTop: 0 }}>小红书帖子与评论</h3>
      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 12, alignItems: "start" }}>
        <div style={{ border: "1px solid #eee", borderRadius: 10, padding: 10 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              value={noteQuery}
              onChange={(e) => setNoteQuery(e.target.value)}
              placeholder="搜索帖子标题/内容/标签"
              style={{ padding: 8, width: "100%" }}
            />
          </div>
          {notesError ? <div style={{ marginTop: 8, color: "crimson" }}>{notesError}</div> : null}
          <div style={{ marginTop: 10, display: "grid", gap: 8, maxHeight: 680, overflow: "auto" }}>
            {notes.map((n) => {
              const active = n.note_id === activeNoteId;
              return (
                <button
                  key={n.note_id}
                  onClick={() => {
                    setActiveNoteId(n.note_id);
                    setOffset(0);
                    setReplyByCommentId({});
                    setReplyErrByCommentId({});
                  }}
                  style={{
                    textAlign: "left",
                    padding: 10,
                    borderRadius: 10,
                    border: active ? "1px solid #333" : "1px solid #eee",
                    background: active ? "#f5f5f5" : "white"
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: 14 }}>{clampText(n.title || "(无标题)", 44)}</div>
                  <div style={{ marginTop: 6, fontSize: 12, color: "#666" }}>{clampText(n.tag_list || "", 60)}</div>
                  <div style={{ marginTop: 6, fontSize: 12, color: "#666", display: "flex", gap: 8 }}>
                    <span>赞 {formatCount(n.liked_count)}</span>
                    <span>评 {formatCount(n.comment_count)}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ border: "1px solid #eee", borderRadius: 10, padding: 12 }}>
          {activeNote ? (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 800, fontSize: 18 }}>{activeNote.title || "(无标题)"}</div>
                  <div style={{ marginTop: 8, whiteSpace: "pre-wrap", color: "#333" }}>{activeNote.desc}</div>
                  <div style={{ marginTop: 8, color: "#666", fontSize: 12 }}>{activeNote.tag_list}</div>
                  <div style={{ marginTop: 8, color: "#666", fontSize: 12, display: "flex", gap: 12 }}>
                    <span>作者：{activeNote.nickname}</span>
                    <span>时间：{formatTs(activeNote.time)}</span>
                    <a href={activeNote.note_url} target="_blank" rel="noreferrer">
                      打开原帖
                    </a>
                  </div>
                </div>
                <div style={{ minWidth: 220, textAlign: "right", color: "#666", fontSize: 12 }}>
                  <div>赞 {formatCount(activeNote.liked_count)}</div>
                  <div style={{ marginTop: 4 }}>评 {formatCount(activeNote.comment_count)}</div>
                  <div style={{ marginTop: 4 }}>藏 {formatCount(activeNote.collected_count)}</div>
                  <div style={{ marginTop: 4 }}>转 {formatCount(activeNote.share_count)}</div>
                </div>
              </div>

              <div style={{ marginTop: 14, padding: 10, border: "1px solid #eee", borderRadius: 10 }}>
                <div style={{ fontWeight: 700 }}>评论分析</div>
                {analyzeError ? <div style={{ marginTop: 8, color: "crimson" }}>{analyzeError}</div> : null}
                {analyze ? (
                  <div style={{ marginTop: 8, display: "grid", gap: 6, fontSize: 13 }}>
                    <div>总评论数：{analyze.total_comments}</div>
                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                      {intentPairs.map(([k, v]) => (
                        <span key={k} style={{ padding: "2px 8px", border: "1px solid #eee", borderRadius: 999 }}>
                          {k} {v}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div style={{ marginTop: 8, color: "#666" }}>加载中…</div>
                )}
              </div>

              <div style={{ marginTop: 14, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                <div style={{ fontWeight: 700 }}>评论列表</div>
                <select value={sort} onChange={(e) => setSort(e.target.value as any)} style={{ padding: 6 }}>
                  <option value="like">按点赞</option>
                  <option value="time">按时间</option>
                </select>
                <input
                  value={commentQuery}
                  onChange={(e) => {
                    setCommentQuery(e.target.value);
                    setOffset(0);
                  }}
                  placeholder="搜索评论内容"
                  style={{ padding: 6, minWidth: 220 }}
                />
                <select
                  value={limit}
                  onChange={(e) => {
                    setLimit(Number(e.target.value));
                    setOffset(0);
                  }}
                  style={{ padding: 6 }}
                >
                  <option value={20}>20/页</option>
                  <option value={50}>50/页</option>
                  <option value={100}>100/页</option>
                </select>
                <button
                  disabled={bulkBusy || !commentsResp?.comments?.length}
                  onClick={bulkSuggest}
                  style={{ padding: "6px 10px" }}
                >
                  {bulkBusy ? `批量生成中 ${bulkProgress.done}/${bulkProgress.total}` : "本页批量生成回复"}
                </button>
              </div>

              {commentsError ? <div style={{ marginTop: 8, color: "crimson" }}>{commentsError}</div> : null}
              {commentsResp ? (
                <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", color: "#666", fontSize: 12 }}>
                    <span>
                      {commentsResp.offset + 1}-{Math.min(commentsResp.offset + commentsResp.limit, commentsResp.total)} / {commentsResp.total}
                    </span>
                    <button
                      disabled={offset <= 0}
                      onClick={() => setOffset(Math.max(0, offset - limit))}
                      style={{ padding: "4px 8px" }}
                    >
                      上一页
                    </button>
                    <button
                      disabled={offset + limit >= commentsResp.total}
                      onClick={() => setOffset(offset + limit)}
                      style={{ padding: "4px 8px" }}
                    >
                      下一页
                    </button>
                  </div>

                  {commentsResp.comments.map((c) => {
                    const reply = replyByCommentId[c.comment_id];
                    const err = replyErrByCommentId[c.comment_id];
                    return (
                      <div key={c.comment_id} style={{ border: "1px solid #eee", borderRadius: 10, padding: 10 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                          <div style={{ color: "#666", fontSize: 12, display: "flex", gap: 10, flexWrap: "wrap" }}>
                            <span style={{ fontWeight: 700, color: "#333" }}>{c.nickname || "匿名"}</span>
                            <span>赞 {formatCount(c.like_count)}</span>
                            <span>{formatTs(c.create_time)}</span>
                            {c.ip_location ? <span>{c.ip_location}</span> : null}
                          </div>
                          <button onClick={() => suggestForComment(c)} style={{ padding: "6px 10px" }}>
                            生成回复
                          </button>
                        </div>
                        <div style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>{c.content}</div>
                        {err ? <div style={{ marginTop: 8, color: "crimson" }}>{err}</div> : null}
                        {reply ? (
                          <div style={{ marginTop: 10, borderTop: "1px solid #eee", paddingTop: 10 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center" }}>
                              <div style={{ fontWeight: 700 }}>建议回复</div>
                              <button
                                style={{ padding: "4px 8px" }}
                                onClick={() => navigator.clipboard.writeText(reply.reply)}
                              >
                                复制
                              </button>
                            </div>
                            <div style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>{reply.reply}</div>
                            <div style={{ marginTop: 8, color: "#666", fontSize: 12 }}>
                              意图 {reply.intent}（{Number(reply.intent_confidence).toFixed(2)}）｜潜客 {reply.lead_level}/{reply.lead_score}｜耗时 {reply.latency_ms}ms
                            </div>
                          </div>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{ marginTop: 10, color: "#666" }}>加载中…</div>
              )}
            </div>
          ) : (
            <div style={{ color: "#666" }}>未选择帖子</div>
          )}
        </div>
      </div>
    </div>
  );
}

