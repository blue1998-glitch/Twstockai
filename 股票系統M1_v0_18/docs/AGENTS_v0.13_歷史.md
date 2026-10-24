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

- Latest version is M1 v0.13; read period_analysis/output/週月均線核心驗收.md and docs/週月均線獨立契約.md; old workflow contracts remain valid.
- Keep evidence staging separate from engine events. Record dates and payment dates are never ex-trading dates.
- Do not retry or bypass the TWSE ex-right endpoint that returned an explicit security denial.
- Core engines use fixed JSON contracts and must remain free of Streamlit/UI dependencies. A local independent research persistence prototype now exists; holdings, formal signal storage and cloud services are not implemented.

- Derivative contract adjustment dates are corroborating evidence, never silently promoted to stock ex-trading dates. X0.00 is not numeric zero.
- Event-ablation replays are engineering comparisons, not approved production inputs. Preserve numeric contracts and versions. The headless calculate/save/read workflow now exists; read-only saved-result browsing/export now exists. Volume-origin wording is corrected in structure-0.3-research, with actual old/new compatibility tests. An independent weekly/monthly aggregation and MA core now exists; main unified-contract/storage/UI integration has not been implemented.

- Keep storage outside numeric engines. Never silently overwrite a stored result or upgrade unverified evidence.
- Use recover on worker startup after interrupted writes; never delete rollback journals or recreate a database to suppress errors.

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
- Next scope: separate immutable file-based period-result save/load/list and read-only display adapter, using the independent result envelope. Preserve all existing SQLite stores/contracts and HTML exports. This is an extension of the independent data layer, not browser-local state. If a shared schema migration becomes necessary, prepare a concrete compatibility proposal first.
