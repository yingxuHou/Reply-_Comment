export type UUID = string;

export type KnowledgeBase = {
  id: UUID;
  slug: string;
  name: string;
  description: string;
  published_version: number;
};

export type SearchHit = {
  chunk_id: UUID;
  revision_id: UUID;
  score: number;
  content: string;
};

export type ReplyResponse = {
  kb_id: UUID;
  kb_version: number;
  intent: string;
  intent_confidence: number;
  reply: string;
  used_knowledge: SearchHit[];
  lead_score: number;
  lead_level: string;
  lead_signals: string[];
  next_actions: string[];
  latency_ms: number;
  created_at: string;
};

export type XhsNote = {
  note_id: string;
  type: string;
  title: string;
  desc: string;
  tag_list: string;
  nickname: string;
  liked_count: string;
  collected_count: string;
  comment_count: string;
  share_count: string;
  time: number | null;
  note_url: string;
  source_keyword: string;
};

export type XhsComment = {
  comment_id: string;
  note_id: string;
  content: string;
  like_count: string;
  create_time: number | null;
  nickname: string;
  user_id: string;
  ip_location: string;
  sub_comment_count: string;
  parent_comment_id: string;
};

export type XhsListNotesResponse = {
  notes: XhsNote[];
  total: number;
  source_files: { contents: string; comments: string };
};

export type XhsListCommentsResponse = {
  note_id: string;
  total: number;
  offset: number;
  limit: number;
  sort: "like" | "time";
  q: string;
  comments: XhsComment[];
};

export type XhsAnalyzeResponse = {
  note_id: string;
  total_comments: number;
  top_comments: XhsComment[];
  intent_counts: Record<string, number>;
  generated_at: string;
};

const API_BASE = (import.meta as any).env?.VITE_API_BASE ?? "/api";

function joinUrl(base: string, path: string) {
  const b = base.endsWith("/") ? base.slice(0, -1) : base;
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${b}${p}`;
}

async function http<T>(path: string, init: RequestInit): Promise<T> {
  const resp = await fetch(joinUrl(API_BASE, path), {
    ...init,
    headers: { "content-type": "application/json", ...(init.headers ?? {}) }
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`${resp.status} ${text}`);
  }
  return (await resp.json()) as T;
}

export const api = {
  listKbs: () => http<KnowledgeBase[]>("/kbs", { method: "GET" }),
  createKb: (payload: { slug: string; name: string; description?: string }) =>
    http<KnowledgeBase>("/kbs", { method: "POST", body: JSON.stringify(payload) }),
  publishKb: (kbId: UUID) => http<{ kb_id: UUID; published_version: number }>(`/kbs/${kbId}/publish`, { method: "POST" }),
  reindexKb: (kbId: UUID) =>
    http<{ kb_id: UUID; kb_version: number; provider: string; model: string; dim: number; indexed_chunks: number }>(
      `/kbs/${kbId}/reindex`,
      { method: "POST" }
    ),
  searchKb: (kbId: UUID, query: string, topK = 5) =>
    http<{ hits: SearchHit[]; latency_ms: number; kb_version: number; query: string; kb_id: UUID; created_at: string }>(
      `/kbs/${kbId}/search`,
      { method: "POST", body: JSON.stringify({ query, top_k: topK }) }
    ),
  replySuggest: (payload: any) => http<ReplyResponse>("/reply/suggest", { method: "POST", body: JSON.stringify(payload) }),
  monitorOverview: (payload: { since?: string; until?: string }) =>
    http<any>("/monitor/overview", { method: "POST", body: JSON.stringify(payload) }),
  xhsListNotes: (q = "") => http<XhsListNotesResponse>(`/xhs/notes?q=${encodeURIComponent(q)}`, { method: "GET" }),
  xhsListComments: (noteId: string, params: { offset: number; limit: number; sort: "like" | "time"; q?: string }) => {
    const qs = new URLSearchParams({
      offset: String(params.offset ?? 0),
      limit: String(params.limit ?? 100),
      sort: params.sort ?? "like",
      q: params.q ?? ""
    });
    return http<XhsListCommentsResponse>(`/xhs/notes/${encodeURIComponent(noteId)}/comments?${qs.toString()}`, { method: "GET" });
  },
  xhsAnalyze: (noteId: string, maxSamples = 500) =>
    http<XhsAnalyzeResponse>(`/xhs/notes/${encodeURIComponent(noteId)}/analyze?max_samples=${maxSamples}`, { method: "GET" })
};
