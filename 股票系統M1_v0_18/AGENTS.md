> 最新P0-3顯示0.2接續root M1_P03_READABILITY_HANDOFF.md及structure_state_chart/READABILITY.md、validation_readability_20261024/驗收報告。只事件可讀性／手機有效繪圖／來源日期及中性量觀察，原核心／JSON／0.1成品完整保留；本輪6 Python／94新腳本Chromium，不與歷史65／94相加。Android未測，下一步只Work看新圖用途差異。下方原文留史。

> 2026-10-24最新：P0-3獨立結構狀態與既有人工模式主圖已接入，讀structure_state/README.md、structure_state_chart/README.md及validation_20261024/驗收報告.md，直接PNG／HTML／JSON／ZIP入口在root deliveries/m1-p03-structure-state-20261024。manual_basis／manual_basis_chart模式切換已實作，不重做；新附層只接受明示來源角色，不等自動選帶或正式策略。真實B88案例是研究角色提案，非人工核定原箱；39新＋26相關Python／94 Chromium實跑通過，Android未測，全部原來源／引擎／庫／歷史限制保持。最新完整Work指令見root M1_P03_STRUCTURE_STATE_HANDOFF.md；下方歷史原文保留。

> 最新獨立人工 Raw／Adjusted 候選主圖在 manual_basis_chart/，外部純解析／保存層在 manual_basis/；先讀 root CONTINUE_IN_WORK_MODE.md 最新節與 manual_basis_chart/README.md／validation_20261022/驗收報告.md。原 0.4.3 及既有引擎／研究數值不改；Adjusted 仍限兩股 283 根現金事件候選，來源缺漏阻擋，Chrome 模擬已驗但 Android 實機未測。最新人工多層箱型判讀另見 root 交接，箱底尚未核定。下方 pressure_chart/ 與其他舊狀態為歷史保留，不覆蓋最新成果。

> 最新交付為pressure_chart/的獨立五年官方Raw／雙維壓力來源主圖；先讀root CONTINUE_IN_WORK_MODE.md最新節、pressure_chart/README.md與validation_20261018/驗收報告.md。四股1213／1214根、244月回應到2026-10-16，原引擎／策略／庫／舊頁與原1490frame數值未變。五年Adjusted／完整公司行動及六日主證未完成；正式高牆／魔王／衰減與增量門檻未知。新頁Android NOT_TESTED_NEW_BUILD，舊technical部分證據分開保留。下方為歷史交接，不覆蓋最新狀態。

> 最新獨立主圖交付：請讀repository root CONTINUE_IN_WORK_MODE.md最上方及本專案 technical_chart/README.md、technical_chart/validation_20261017/驗收報告.md。新頁technical-chart-view/0.1直接呈現真實日K／量／MACD、導航、原保存證據與JSON。1101／2884僅179根、6488／8069僅283根，無多年或真實盤中。新主圖Android NOT_TESTED；舊嘗試頁PARTIAL_EVIDENCE_OBSERVED獨立保留。原引擎、策略、schema、庫與舊頁不改；下方舊狀態按其歷史時點閱讀。

# Project instructions

- Latest attempt-core integration is a NEW opt-in page via product_candidate/attempt_view.py and attempt_template.html / attempt_viewer.js. Read product_candidate/ATTEMPT_VIEW.md and validation_attempt_view_20261017/驗收報告.md. It only enables explicitly synthetic fixtures, not real market authentication or automatic references. The original attempt core and all old candidate calculation/view sources remain immutable. Latest tests: 325 Python, 28 source/core prefix checks, real Chromium87 / 56 exact downloads; physical Android and product/trading acceptance remain unvalidated.

- Latest authorized product work is additive v0.19 in product_candidate/ (directory name remains v0.18). Read root CONTINUE_IN_WORK_MODE.md, M1_V018_PRODUCT_GAP_HANDOFF.md, M1_V019_REQUIREMENTS_TRACE.md and product_candidate/README.md first. Latest feedback supersedes historical Android-only/no-new-stage restrictions below. This is not approval of new strategy thresholds or core lifecycle definitions.
- The independent explicit offline candidate producer reads original stores and projects newly labelled candidate OHLC/MACD; it never changes old engines, schemas, stores or pages. Its UI performs no analysis calculation. Product/lifecycle/pattern acceptance remains unknown, classification NOT_VALIDATED, trades NOT_EVALUATED. Final real Chromium checks are PASS, physical Android NOT_TESTED; historical BLOCKED notes below describe earlier environments. See product_candidate/validation_20261017/驗收報告.md. Standing GitHub branch file-delivery authorization from root AGENTS applies; deployment/payment/trading/messages and subagents remain prohibited.

- User-authorized saved-evidence annotations are now implemented in 日週月研究對照_結構標記_v0_18.html; read docs/結構標記顯示契約.md and annotations/validation_20261017/驗收報告.md. The two reference diagrams are visual input, not authority to invent long-candle resistance, platform-breakout or failed-rebound rules. Only daily saved pivots/zones are overlaid. Original pages and numeric data stay immutable. New-page real Chromium acceptance is now PASS via loopback HTTP; physical Android is still NOT_TESTED.

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
