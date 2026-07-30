# IncidentIQ — Frontend Plan (React, standalone)

**Do first:** `node --version` (need 18+). Then paste PROMPT F0 into Claude Code.

This plan is independent of the backend. Phase F1 builds a mock API server that fakes every endpoint, so you build and demo the entire UI before the real backend exists. Swapping to the real backend at the end is one config line. ~4.5 hours, 6 phases, each = one Claude Code prompt + a check.

---

## THE FROZEN API CONTRACT (do not change without telling the backend dev)

Base URL from `VITE_API_BASE` env var. Mock serves :8501, real backend :8500.

```
POST  /incidents/upload                multipart "file" →
      202 {incident_id, event_count, unparsed_count, severity, duration_s, cached}
GET   /incidents/{id}/generate         SSE stream, event types:
      stage        {name: "parsing"|"masking"|"generating_title"|"generating_summary"|"generating_impact"|"generating_rca"|"generating_recommendations", detail}
      token        {section, text}
      section_done {section: SectionResult}
      done         {report: Report}
      error        {message, recoverable}
GET   /incidents                       [{incident_id, created_at, title, severity, category, duration_s, status}]
GET   /incidents/{id}                  {report: Report, events: [Event], debug: {digest, models: {section: model}, latencies_ms, retries, validation}}
PATCH /incidents/{id}/sections/{kind}  {content} → 200 | 409 if finalized
POST  /incidents/{id}/finalize         200
GET   /incidents/{id}/export?format=md|html   file download
GET   /incidents/{id}/similar          [{incident_id, title, severity, score}]
GET   /analytics/summary               {kpis: {total, sev1, avg_mttr_s, recurring_pct},
                                        severity_mix: [{severity, count}],
                                        by_category: [{category, count}],
                                        over_time: [{date, count}],
                                        recurring_causes: [{label, count}]}
POST  /seed                            SSE: progress {done, total} … done
GET   /health                          {status, ollama, models}

Report: {incident_id, created_at, title, severity: SEV1-4, category, status: draft|finalized,
         started_at, ended_at, duration_s, source_filename,
         sections: {summary|impact|rca|recommendations: SectionResult}}
SectionResult: {kind, content, confidence: High|Medium|Low|null, evidence_ids: [], model, validated, error}
Event: {id: "E-0001", ts, severity, host_token, service, message_masked, raw_line_no}
Errors: {status: "failed", message, detail} with real HTTP codes. Never HTML error pages.
```

---

## PROMPT F0 — Scaffold (15 min)

```
npm create vite@latest frontend -- --template react, then npm install react-router-dom recharts.
Structure:
src/
├─ api/client.js         # fetch wrapper reading VITE_API_BASE (default http://localhost:8501), JSON + error normalization
├─ api/sse.js            # EventSource helper: subscribe(url, {onStage,onToken,onSectionDone,onDone,onError})
├─ pages/NewIncident.jsx  History.jsx  Dashboard.jsx  About.jsx
├─ components/           # empty
├─ styles/tokens.css     # severity colors + spacing vars (below)
└─ App.jsx               # react-router sidebar layout, 4 routes, HealthDot polling GET /health every 10s

tokens.css: --sev1:#D32F2F --sev2:#F57C00 --sev3:#FBC02D --sev4:#78909C; dark-friendly neutral background; system font stack. Operational-dashboard look, no CSS framework.
.env.development: VITE_API_BASE=http://localhost:8501
```

**Check:** `npm run dev` → sidebar + 4 empty routes render, HealthDot shows red (nothing on :8501 yet — correct).

---

## PHASE F1 — Mock API server (30 min)

Your backend-independence layer. Everything after this builds against it.

```
Create mock/server.js (node, express + cors — npm i -D express cors) serving the full contract above on :8501:
- 12 hardcoded realistic incidents in mock/fixtures.js: varied severity/category (disk exhaustion x2 for similarity demo, OOM, network partition, cert expiry, DB pool, failed deploy...), full Report + Event + debug payloads
- POST /incidents/upload → 202 after 400ms fake delay; special case: filename containing "garbage" → 422 {status:"failed", message:"File could not be parsed", detail}
- GET /incidents/{id}/generate → SSE that replays a realistic sequence over ~8 seconds: stage events, then token events streaming the RCA text word by word, section_done per section, final done. One fixture must include confidence:"Low" + validated:false (to exercise the amber border) and evidence_ids referencing real fixture event ids.
- PATCH persists in memory; finalize flips status; 409 after finalize
- /analytics/summary computed from fixtures; /similar returns the disk-exhaustion sibling at score 0.83
- /seed → SSE progress 1..12 then done
- npm script: "mock": "node mock/server.js"
```

**Check:** `npm run mock` + `curl -N localhost:8501/incidents/INC-1/generate` shows staged SSE ending in `done`; HealthDot in the app turns green.

---

## PHASE F2 — Upload + live generation view (60 min)

The demo centerpiece. Get the streaming feel right here.

```
Build NewIncident.jsx:
1. UploadDropzone — drag-drop + picker + 3 "sample file" buttons; client-side reject >5MB and non-text with inline message
2. On 202 → GenerationProgress:
   - Staged checklist from stage events: "Parsing… 412 events" → ✓, active stage gets a spinner
   - Live tokens: append to a ref buffer, flush to state every 100ms (never setState per token), autoscrolling monospace pane for the section currently generating
   - error event → amber banner {message, what still works, Retry button}; recoverable:false hides retry
3. On done → mount ReportView (Phase F3) with the report payload
4. cached:true on upload → skip straight to ReportView (no fake progress)
State: keep currentIncident in a context provider so History can reuse ReportView.
```

**Check:** upload any file against mock → watch stages tick + RCA stream in over ~8s → report appears. Upload "garbage.txt" → amber banner, no blank screen, no console errors.

---

## PHASE F3 — ReportView with tabs (60 min)

```
ReportView (report, events, debug, readOnly) with three tabs:

Report tab:
- Header: title, SeverityBadge (color + text label always), duration chip, status chip
- Sections: summary, impact, RcaCard, RecommendationsChecklist
- RcaCard: content, ConfidenceMeter (High/Med/Low styling), EvidenceChips — click scrolls Timeline tab to that event row and flash-highlights it
- Any section with confidence Low OR validated:false → amber left border + "review required" label
- Per-section Edit toggle (textarea) → PATCH on save; hidden when readOnly or finalized
- Toolbar: Save Draft, Finalize (confirm dialog: "Finalizing locks all edits"), Export MD, Export HTML (both hit export endpoint, trigger download)

Timeline tab: table (ts, SeverityBadge, host_token, service, message_masked), severity filter pills, row ids anchor-able for evidence chips. 400+ rows → simple windowing or paginate at 200.

Debug tab (the judge tab): masked digest in a <pre>, per-section table (model, latency ms, retries, validated), validation flags. Label it "AI Transparency".
```

**Check:** all three tabs render from mock fixture; evidence chip click jumps + highlights; edit → save → reload → edit persisted (mock memory); finalize → edits lock + PATCH returns 409 handled gracefully.

---

## PHASE F4 — History + Dashboard (50 min)

```
History.jsx:
- GET /incidents table: date, title, SeverityBadge, category, duration, status; desc order; severity filter pills; search-by-title input
- Row click → GET /incidents/{id} → ReportView readOnly={status==='finalized'}
- SimilarPanel under the report: GET similar → cards (title, badge, score %) → click-through navigates
- Empty list → "Seed demo data" button → POST /seed SSE progress bar → refresh

Dashboard.jsx (recharts):
- KPI row: total, SEV1 count, avg MTTR (format s → "1h 12m"), % recurring
- SeverityDonut, CategoryBar, IncidentsOverTimeLine, RecurringCausesBar — severity colors from tokens.css, category bars neutral
- Each chart wrapped in ChartCard with a "view data" expander rendering the raw rows as a table (accessibility + judge trust)
- Empty data → seed button, loading → skeleton cards, fetch fail → amber banner per card (one dead chart must not kill the page)
```

**Check:** seed via History → table fills; disk-exhaustion incident shows its sibling at 83%; Dashboard renders 4 charts + KPI row from mock; kill the mock server → banners, not white screen.

---

## PHASE F5 — About page + polish + real-backend swap (45 min)

```
1. About.jsx: architecture diagram (inline SVG: Upload → Parser → Masker → SLM pipeline → Validator → Report, side rails for SQLite + Ollama), model-routing table, privacy statement ("all inference local · identifiers masked before AI · zero network egress"), stack list.
2. Polish pass: consistent spacing via tokens, focus states on all interactive elements, SeverityBadge never color-only, page titles, favicon.
3. Loading/empty/error audit: every page has all three states — list any gaps and fix.
4. Swap test: .env.production or runtime toggle VITE_API_BASE=http://localhost:8500. Document in README: "mock: npm run mock + npm run dev · real: set VITE_API_BASE and start backend".
5. Print a frontend demo checklist: upload → streaming → tabs → garbage file → History → similar → Dashboard → About.
```

**Check:** full click-through against mock with zero console errors; flip VITE_API_BASE to :8500 → app boots and HealthDot reflects real backend state (red is fine if backend isn't ready — the point is nothing crashes).

---

## Integration with backend (15 min, when backend Phase 5 is done)

1. Set `VITE_API_BASE=http://localhost:8500`, start real backend.
2. Run the demo checklist end to end.
3. Any mismatch = contract violation — diff the real response against this doc's contract, fix on whichever side deviated. The contract wins, not the code.

## Cut order if behind

1. Search-by-title in History
2. Evidence-chip scroll+highlight (keep plain chips)
3. Chart data expanders
4. HTML export button (keep MD)
5. Never cut: SSE streaming view, Debug tab, error banners, mock server — the demo depends on these.

## Rules

- One phase = one Claude Code task → review diff → run check → commit.
- Mock server is disposable scaffolding: never import fixture data into src/, only fetch it.
- Ref-buffered token flush is non-negotiable — per-token setState will stutter on the lab machine.

**Next action:** `node --version`, then paste PROMPT F0.
