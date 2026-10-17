# Project instructions

- This is a Traditional Chinese stock-system research prototype for a non-engineer user.
- Preserve independent numeric engines. UI renders their outputs; no LLM-generated core numbers or states.
- Read README.md, docs/候選規則_v0.1.md and docs/CODEX交接.md first.
- Core thresholds are research candidates, not accepted strategy rules. Do not silently promote them.
- Record occurred_at, first_observed_at and confirmed_at separately. Never overwrite past snapshots.
- Keep Raw and adjusted candidate modes separate, including corporate-action boundary handling.
- Never infer intraday ordering from daily OHLC, fabricate missing prices, infer ordinary-stock status from code length, or present unverified backtest performance.
- No trading qualification exists in this version. Keep NOT_EVALUATED until its own necessary conditions and tests are explicitly defined.
- State actual test execution and limits honestly. Browser tests are prepared but were blocked by missing browser executable in the originating environment.
- User authorizes routine implementation, diagnosis and reversible fixes without repeated questions. Ask only for core strategy decisions, major architecture changes or actions requiring explicit authorization.
- Do not publish, deploy, send messages, place trades or connect paid market services under this handoff.
- Do not spawn parallel agents under this file; ordinary local execution is sufficient.

- Latest UI version is M1 v0.18 (mobile readability only); read docs/手機顯示修正_v0.18.md and docs/CODEX交接.md first, followed by docs/日週月唯讀對照契約.md. Old contracts remain valid.
- Keep evidence staging separate from engine events. Record dates and payment dates are never ex-trading dates.
- Do not retry or bypass the TWSE ex-right endpoint that returned an explicit security denial.
- Core engines use fixed JSON contracts and must remain free of Streamlit/UI dependencies. A local independent research persistence prototype now exists; holdings, formal signal storage and cloud services are not implemented.

- Derivative contract adjustment dates are corroborating evidence, never silently promoted to stock ex-trading dates. X0.00 is not numeric zero.
- Event-ablation replays are engineering comparisons, not approved production inputs. Preserve numeric contracts and versions. The headless calculate/save/read workflow now exists; read-only saved-result browsing/export now exists. Volume-origin wording is corrected in structure-0.3-research, with actual old/new compatibility tests. An independent weekly/monthly aggregation and MA core now exists; main unified-contract/storage/UI integration has not been implemented.

- Keep storage outside numeric engines. Never silently overwrite a stored result or upgrade unverified evidence.
- For existing SQLite workers, use recover on startup after interrupted writes; never delete rollback journals or recreate a database to suppress errors. The independent period file store uses one exclusive immutable-file commit and reports unpublished pending files without automatic cleanup.

- Workflow completion is not classification approval. Preserve NOT_SAVED/UNKNOWN/COMMITTED semantics and use LOOKUP/READ after response failures.
- READ/LOOKUP and UI browsing must not recompute or silently choose a newer rule version.

- Saved viewer exports only AnalysisStore public read-only methods. Never invoke recovery or a numeric engine from browsing/export. If a hot journal blocks a read, fail explicitly and preserve all files; separate worker recovery is required.
- Offline viewer embeds exact saved bundles. Keep original viewer unchanged. Plot stored MA curves only; raw source OHLC is separately labeled. Never synthesize adjusted OHLC or new pivots in JS.
- Native SHARES_REPORTED source volume is correct, but legacy structure evidence.volume_precision may falsely say lots scaled. Disclose this issue; keep stored old results immutable. A correction must have a new producer version, retain old snapshots and prove numeric equality.

- Public structure.analyze now requires explicit volume_unit (missing/unsupported yields DataError). JSON job contracts already required source.volume_unit. Never rescale volume to fix provenance wording. The new unit is in structure snapshot IDs; parameters and numeric rules are unchanged.
- Use volume_revision/run_acceptance.py for current acceptance. Old v0.9/v0.10 acceptance runners are version-gated before writes; they are historical, not current regeneration commands.
- Historical v0.9/v0.10 databases and both old HTML exports remain immutable artifacts. Actual old/new results live in the independent volume_revision/output database; multiple matches require explicit version selection.
- Weekly/monthly work should start as independent pure modules/contracts; do not silently add components to stock-analysis/1.0, whose storage contract requires exactly structure and daily_ma. Never claim a partial week/month complete or replace insufficient windows with zero.

- Period engine is src/period_ma.py with standalone src/period_jobs.py. Do not add it silently to stock-analysis/1.0 or analysis-store/1.0. Candidate including-open and elapsed-calendar-only values must remain separate.
- Period as_of means end of the date, using assumed closed daily source records. Sunday is ISO week end; month end uses Gregorian calendar. Elapsed is not authenticated market-calendar completeness.
- Unknown missing periods, supplied-calendar mismatches and uncertain left edges break SMA windows. Only a fully covered elapsed period with zero expected trading dates in the supplied unverified calendar can be skipped without a synthetic close.
- Independent period save/load/list/lookup and read-only export now exist in period_store*, period_viewer*. Real 12-result acceptance exists; browser/mobile rendering remains NOT_TESTED. Preserve every old SQLite store/contract and HTML. The external period workflow now exists; only explicit RUN may lazy-import/call the core. Current IMPORT worker remains compatible. The authorized daily/weekly/monthly comparison integration is now delivered with exact source/anchor checks, explicit version selection, charts, original evidence and JSON export. No automatic calculation, nearest date, latest version or combined trading conclusion. Remaining browser/physical phone QA is explicitly blocked/untested, not a reason to invent more routine engineering stages. If a shared schema migration becomes necessary, prepare a concrete compatibility proposal first.

- Period file-store reads/export must not import numeric engines, clean pending files, repair content or choose a newer version/date. Same identity with different result or reason is a conflict, not an overwrite. Unknown producer versions fail closed. After UNKNOWN or response-output failure use explicit READ/LOOKUP. No multi-process initialization guarantee; initialize the store before concurrent imports. See filesystem/durability limits in the independent contract.

- src/period_workflow.py and period_workflow_cli.py are an external coordinator, not a new numerical producer. Explicit RUN calculates once per request, then validates/saves/reads back; repeated RUN recalculates and storage deduplicates. READ/LOOKUP never import engines. Preserve stage-specific NOT_SAVED/UNKNOWN/COMMITTED and read-only NOT_APPLICABLE. A read-back or output failure after confirmed save must not lose COMMITTED or fall back to in-memory results.
- Keep v0.15 background store and all previous stores immutable. New cross-timeframe views must first prove same code/exchange/mode/as_of/source/volume/prefix-events/adjustment anchor; missing or conflicting matches are visible restrictions, never a license to calculate or pick a newer result.

- Cross-view reads use only public read-only store methods; never import engines, RUN adapters, or recovery. New missing daily calculations are isolated in cross_view/prepare_daily.py and the separate supplement DB, with fresh-process full-result verification before PASS.
- A rollback-journal incident occurred in the new supplement DB; explicit existing recovery and re-save restored three readable records, but root cause is NOT_ESTABLISHED. Retain diagnostics. Reader must fail without repairing; do not delete journals or silently regenerate.
- New view compares independent saved results, not trading direction. Conflicts block joint charts; partial views are visibly partial. Legacy volume-provenance warnings and unrecorded adjusted daily OHLC remain visible. Physical Android and real browser must never be inferred from DOM/canvas doubles.

- v0.17 is diagnostic closure, not a new strategy/UI/storage stage. Read docs/SQLite事件診斷與接續驗收.md and reliability/output/SQLite故障重現驗收.json. All previously delivered src modules and saved numeric artifacts remain unchanged.
- reliability/sqlite_probe.py observes existing files with mode=ro and outputs extended SQLite errors plus before/after hashes. It refuses WAL header/sidecars before SQLite connect (READ_REFUSED_WAL) to avoid shared-memory side effects; no immutable bypass. It never recovers; READABLE is not full AnalysisStore validity. It is not a coherent live backup. Stop writers before collecting incident evidence; preserve database and all sidecars together.
- reliability/run_acceptance.py injects faults only into temporary copies, never user paths. Matching SQLITE_READONLY_ROLLBACK symptoms do not establish the historical cause or explain lost data after reported COMMITTED. Do not label that root cause fixed.
- The complete development handoff is ready for a Codex environment with an existing Chromium executable. Such an environment has not been connected or verified here. No need to invent additional features to fill a blocked browser stage. Physical Android still requires separate actual-device QA.

- v0.18 follows three actual Android screenshots of the old page and the user's download report. Old-page opening and daily/weekly/monthly rendering were directly observed; download works by user report, but its type/content was not independently verified. The new page's physical-device validation is NOT_TESTED.
- Use 日週月研究對照_手機版_v0_18.html for the updated display. Preserve 日週月研究對照.html and all historical stores/results. Ordinary displayed prices/MAs use two decimal places with decimal-string half-up rounding; original data and JSON exports retain exact stored strings. Nulls remain null with reasons. Never reduce internal precision to satisfy a display preference.
- Responsive canvas backing follows actual CSS dimensions and device pixel ratio. This is a display transform, not a new numeric engine or adjusted-OHLC calculation. Keep red-up/green-down, null gaps, and exact version/date selection.
- Cross-view CLI --mobile requires --html. The default renderer still reproduces the original HTML. Both templates must be protected from output collisions. Numeric contracts, databases and rule versions are unchanged.
- Browser emulation is BLOCKED here without an existing Chromium; do not present Node VM/canvas doubles as layout/touch verification. Do not invent new routine stages while blocked. Follow docs/CODEX交接.md for the concrete browser acceptance task.
