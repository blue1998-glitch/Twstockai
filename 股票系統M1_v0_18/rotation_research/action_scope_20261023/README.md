# 公司行動適用對象／版本核對 0.3

本輪獨立程式入口；接續983b3559b616703e705bd64a70d256e4a09bbe03的Work來源核對，不改舊producer或資金帳。來源缺口仍會拒算，沒有新市場績效或UI。

- [實作及實測報告](REPORT.md)、[數值／來源契約](CONTRACT.md)、[完整續接指令](WORK_HANDOFF.md)。
- [新catalog與來源欄位](events-v03.json)：5個原帳組件、5個來源版本（3組文件家族，非5個獨立公司行動）。
- [72窗口新資格結果](window-qualification.json)、[單一跨換股日probe](scope-refusal.json)、[執行摘要](verification.json)、[24測試](tests.log)。
- 原來源在source_review_20261022；新producer校驗六原件、metadata、抽字及實際PDF連結，並與Work的直接比例欄位比對。
- 可下載小包／逐檔遠端核對入口：根deliveries/m1-action-scope-20261023/README.md。

解壓至新資料夾，標準Python離線重現：
```bash
cd 股票系統M1_v0_18
python3 -m unittest rotation_research.test_action_scope -v
python3 -m rotation_research.action_scope_sources
```
無新依賴、網路查詢或瀏覽器。source producer只寫本新目錄；純數值action_scope.py不讀檔、不連網、不選策略。

進階查單一欄位時，先從events-v03.json明確選inventory版本與field，提供family／issuer_code／entitled_old_code／action_type／old_instrument／version_id、field／unit／date_role、帶時區observed_as_of及purpose=SOURCE_DIAGNOSTIC，再呼叫action_scope.resolve_field。它不自行選最新版本；FINAL_LEDGER使用另需最終欄位資格，當前部分來源不具此資格。
