import { KNOWLEDGE } from "../lib/knowledge.js";
import { MODES, SEARCH_RULES, NO_SEARCH_RULES } from "../lib/modes.js";

const MODEL = process.env.MODEL || "claude-sonnet-5-5";
const MAX_TURNS = 16;
const MAX_CHARS = 4000;
const MAX_SEARCHES = Number(process.env.MAX_SEARCHES || 3);
const SEARCH_ON = process.env.WEB_SEARCH !== "off";
const RS = "\u001e"; // record separator: wraps status events inside the text stream

function parseCodes() {
  const map = new Map();
  for (const pair of (process.env.ACCESS_CODES || "").split(",")) {
    const [label, code] = pair.split(":").map(s => (s || "").trim());
    if (label && code) map.set(code, label);
  }
  return map;
}

export default async function handler(req, res) {
  if (req.method !== "POST") { res.status(405).json({ error: "Use POST." }); return; }
  let body = req.body || {};
  if (typeof body === "string") { try { body = JSON.parse(body || "{}"); } catch { body = {}; } }
  const { code, messages, mode, check, web } = body;

  const who = parseCodes().get(String(code || "").trim());
  if (!who) { res.status(401).json({ error: "That access code isn't valid." }); return; }
  if (check) { res.status(200).json({ ok: true, name: who, search: SEARCH_ON }); return; }
  if (!process.env.ANTHROPIC_API_KEY) { res.status(500).json({ error: "The server has no API key set." }); return; }
  if (!Array.isArray(messages) || !messages.length) { res.status(400).json({ error: "No message." }); return; }

  let turns = messages
    .filter(m => m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string" && m.content.trim())
    .map(m => ({ role: m.role, content: m.content.slice(0, m.role === "user" ? MAX_CHARS : 12000) }))
    .slice(-MAX_TURNS);
  while (turns.length && turns[0].role !== "user") turns.shift();
  if (!turns.length || turns[turns.length - 1].role !== "user") { res.status(400).json({ error: "Last message must be yours." }); return; }

  const allowSearch = SEARCH_ON && web !== false;
  const modeText = MODES[mode] || MODES.explore;
  const last = turns[turns.length - 1];
  turns[turns.length - 1] = { role: "user", content: `${modeText}\n\n${allowSearch ? SEARCH_RULES : NO_SEARCH_RULES}\n\nUser message:\n"""${last.content}"""` };

  const payload = {
    model: MODEL, max_tokens: 3500, stream: true,
    system: [{ type: "text", text: KNOWLEDGE, cache_control: { type: "ephemeral" } }],
    messages: turns
  };
  if (allowSearch) payload.tools = [{ type: "web_search_20250305", name: "web_search", max_uses: MAX_SEARCHES, user_location: { type: "approximate", country: "US" } }];

  let upstream;
  try {
    upstream = await fetch(process.env.ANTHROPIC_URL || "https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "content-type": "application/json", "x-api-key": process.env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01" },
      body: JSON.stringify(payload)
    });
  } catch { res.status(502).json({ error: "The agent couldn't be reached. Send again." }); return; }

  if (!upstream.ok || !upstream.body) {
    const detail = await upstream.text().catch(() => "");
    console.error("anthropic_error", upstream.status, detail.slice(0, 500));
    const msg = upstream.status === 429 ? "The agent is busy. Wait a moment and send again."
      : upstream.status === 401 ? "The server's API key was rejected."
      : upstream.status === 404 ? "The model name isn't available. Check the MODEL setting."
      : /web_search|tool/i.test(detail) ? "Web search isn't enabled for this API key. Turn it on in the Anthropic Console, or switch web search off."
      : "The agent couldn't answer. Send again.";
    res.status(502).json({ error: msg }); return;
  }

  res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no" });
  const event = o => res.write(RS + JSON.stringify(o) + RS);

  const blocks = {};            // index -> {type, json}
  const retrieved = new Map();  // url -> {title, page_age}
  let fullText = "", searches = 0, stop = "";
  const reader = upstream.body.getReader(), dec = new TextDecoder();
  let buf = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf("\n\n")) >= 0) {
        const block = buf.slice(0, i); buf = buf.slice(i + 2);
        const line = block.split("\n").find(l => l.startsWith("data:"));
        if (!line) continue;
        let ev; try { ev = JSON.parse(line.slice(5).trim()); } catch { continue; }
        if (ev.type === "content_block_start") {
          const cb = ev.content_block || {};
          blocks[ev.index] = { type: cb.type, json: "" };
          if (cb.type === "web_search_tool_result") {
            if (Array.isArray(cb.content)) {
              for (const r of cb.content) if (r.url) retrieved.set(r.url, { title: r.title || "", page_age: r.page_age || "" });
              event({ event: "results", n: cb.content.length });
            } else event({ event: "search_error", code: cb.content?.error_code || "unknown" });
          }
        } else if (ev.type === "content_block_delta") {
          const d = ev.delta || {};
          if (d.type === "text_delta") { fullText += d.text; res.write(d.text); }
          else if (d.type === "input_json_delta" && blocks[ev.index]) blocks[ev.index].json += d.partial_json || "";
        } else if (ev.type === "content_block_stop") {
          const b = blocks[ev.index];
          if (b?.type === "server_tool_use") {
            searches++;
            let q = ""; try { q = JSON.parse(b.json || "{}").query || ""; } catch {}
            event({ event: "search", query: q });
          }
        } else if (ev.type === "message_delta") {
          stop = ev.delta?.stop_reason || stop;
        } else if (ev.type === "error") {
          res.write("\n\n[The answer was interrupted. Send again.]");
        }
      }
    }
  } catch { res.write("\n\n[The answer was interrupted. Send again.]"); }

  event({ event: "sources", urls: [...retrieved.entries()].map(([url, m]) => ({ url, ...m })) });
  if (stop === "pause_turn" || stop === "max_tokens") event({ event: "incomplete", reason: stop });

  // Log usage and any new findings as candidates for the library (read them in Vercel logs).
  let newFindings = [];
  const m = fullText.match(/<cards>([\s\S]*?)<\/cards>/);
  if (m) { try { newFindings = (JSON.parse(m[1].trim()).new || []); } catch {} }
  console.log(JSON.stringify({ at: new Date().toISOString(), user: who, mode: mode || "explore", searches, new_findings: newFindings.length }));
  for (const f of newFindings) console.log("CANDIDATE_INSIGHT " + JSON.stringify({ ...f, url_retrieved: retrieved.has(f.url), user: who, at: new Date().toISOString() }));
  res.end();
}
