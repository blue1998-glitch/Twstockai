# Twstockai: start here

The latest delivered implementation is M1 v0.18. The root v0.17 ZIPs are immutable historical inputs, not the current working source tree.

1. Before editing, run `python3 codex/bootstrap_m1.py` from this repository root. It checks the three existing ZIP fingerprints, applies the versioned update, builds the mobile HTML from the exact saved catalog and verifies 852 files. It uses the standard library and needs no downloads or API keys.
2. If it reports PREPARED or ALREADY_PREPARED, use `股票系統M1_v0_18/` as the working directory. Read its AGENTS.md, README.md, docs/CODEX交接.md and mobile_viewer/output/手機顯示修正驗收.md before working.
3. PREPARATION_FAILED means stop and inspect the explicit error. Do not delete an existing working directory or overwrite changed files to silence a fingerprint mismatch. Existing modifications must be reviewed and preserved.
4. The concrete remaining task is new-page real-browser acceptance using an existing Chromium, followed by new-version physical Android QA. The delivered 265 Python tests passed; do not repeat unchanged core tests without a reason. New browser acceptance is currently BLOCKED, not PASS. Use the commands and boundaries in the project handoff.
5. Keep numeric engines independent of UI; display prices/MAs with two decimals while retaining full stored/download precision. Nulls, exact dates/versions, Raw/Adjusted restrictions, historical stores, NOT_VALIDATED and NOT_EVALUATED remain unchanged.
6. User authorizes routine reversible implementation and diagnosis. Ask only for core strategy, major architecture or genuinely necessary authorization. Do not deploy, pay, trade, send messages, or spawn subagents.
7. Keep source changes reviewable in Git. The ZIP update is a verified initial import, not a reason to keep future code hidden inside archives. Speak Traditional Chinese and finish by stating whether the user should continue in Work Mode or Codex.

After the initial import, Git contains editable v0.18 source but omits historical data/build outputs. On an existing or fresh source checkout use `python3 codex/bootstrap_m1.py --hydrate-missing` to verify a private baseline and restore missing assets only. It reports and preserves differing source files; it does not certify them against the historical manifest. The default command remains a strict baseline check and must not be used to overwrite development changes. Read `股票系統M1_v0_18/docs/結構標記顯示契約.md` and the latest acceptance report for the saved-evidence annotation page. Do not calculate new strategy states from example images.
