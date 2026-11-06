# 2026-10-20 Work｜追溯診斷實讀與結構判讀（非核心規則）

Scope: READ_ONLY_COMPARISON_NOT_APPROVED_RULE. Base branch head ef38c4ae589249a0d003f6baba1155ce2639e400, artifact 57e3d9e55c226c5dd0e69fcbd26883d0da81667e. No core/parameters/result changes, no new tests.

## 已核來源
GitHub connector讀AGENTS.md、CONTINUE_IN_WORK_MODE.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md、deliveries/m1-v019-graph-diagnostics-20261019/{WORK_HANDOFF.md,README.md,GITHUB_DOWNLOAD_VERIFICATION.json}、graph_diagnostics/{README.md,generated/review-diagnostics.json,validation_20261019/驗收報告.md}、docs/visual-discussion/20261019_graph_core_review/{README.md,structural-comparison.json,browser-observation.json,WORK_HANDOFF.md}。先前87檔/70,735,165 bytes為歷史Codex收據，本輪未重新下載核對87檔。

## 判讀
B77 6%來源2023-10-24～2025-03-12，2025-03-24才確認。向左枚舉至2023-05-02的串高群6.05、容許3.5700、餘量-2.4800；2023-05-02高40.25與2024-09-30、11-25高34.20為證人。向右至2025-04-08低群3.25、容許2.4675、餘量-0.7825。僅是原轉折枚舉串被研究幾何拒絕；2023-06人工月份起點未必是已確認轉折，不能聲稱人工月份主帶本身被拒。

B44/B80跨尺度四來源同幾何，來源2025-04-08～05-13共25筆，分別2025-05-14、05-27確認；2025-06-02研究離箱/破底不等來源末轉折或人工整箱終點。人工2025-04-07～06-02共39筆及5/13局部代表保留；6/3為前箱破底K且不屬現箱。原UI未選不等未檢出。

B67→68→70→72→74→76→77同尺度來源ID前綴版本，跨尺度同幾何與B89不同起點局部串另列；89候選版本與84幾何組都非獨立型態數。B77原32廣義後來候選非直接承接，direct_successor_id=null。B77/B44/B80/B88後續觀察383/349/340/31筆、至最低163/129/120/11筆，非公平等窗重要性。B88的1/27=26.95事後確認、10/12～16越過/跌回序列保留。

## 待研究（非核准方案）
應先辨識長期結構是否可能由不同價格層級、局部箱、轉折演化構成，再研究跨尺度主次、局部箱歸屬與破底後承接；不靠調35%或3/6/12%湊人工答案、不寫死人工日期、不由parent或successor推正式重要性。正式區界/量口徑/增量/衰減/重要性/合併/直接承接/生命階段未定，primary_pressure_id=null。

## 驗證限制
本輪僅GitHub文字/JSON讀取及分析；沒有本地bootstrap、Python、Chromium、Android或新圖片驗收。原35 Python、60+60+60及45 Chromium/12下載是先前Codex報告，不是本輪重跑。Android NOT_TESTED_NEW_BUILD；file://不重試不繞過。Raw公司行動、五年Adjusted、歷史可得、SQLite根因未知。原引擎/策略/庫/歷史/舊頁/案例/圖片保留，main不動。
