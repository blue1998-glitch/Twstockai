請接續股票系統M1，先補新自動辨識的可追溯診斷，不調參湊人工答案。

儲存庫blue1998-glitch/Twstockai，分支dev/m1-v018-chart-annotations。確認包含成品2d480bffcaebfa09768e04a283227effc3fc0a00及交接fb94be48122737271541ab21488cd04efa7a484a；讀分支最新後續成果並保留，不用main或舊ZIP覆蓋。

依序實讀AGENTS.md、CONTINUE_IN_WORK_MODE.md頂端、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節、docs/visual-discussion/20261019_graph_core_review/README.md及structural-comparison.json／browser-observation.json／本WORK_HANDOFF、PROJECT_VISION.md／M1_V019_VISUAL_RULE_NOTES.md最新要求，再讀graph_core及graph_core_chart README、原recognition-audit、核心原碼及原交付WORK_HANDOFF。工程執行前在本checkout按AGENTS重跑bootstrap --hydrate-missing，保留差異；別沿用其他環境狀態。

Work已實下載核新ZIP／9成員CRC及SHA、原HTML與core JSON全等，有限Chromium133 HTTP實看5圖／0pageerror，沒有重算核心、沒有重跑Codex21／60／115／72，也不是Android。新判讀是助手分析未獲使用者批准。原0.4.3樣式已收束，不重開；101圖片與私人Drive逐圖資料不重讀不公開。

具體可重現差異：
1.B77=6%／2023-10-24～2025-03-12／333筆，3/24確認。並非2023-06～2025-04月份整體主帶；463完整月份閱讀中左97／右33只是顯示差異，不是正式成員或accuracy。需診斷哪些已確認轉折／候選串被何條件拒絕或未選；不要把月初月底寫成答案。
2.B44／B80都為4/8～5/13／25筆，研究界28.45～31.40，分別5/14／5/27確認；四來源轉折日期／種類／價位相同。source_end是末轉折，path first_departure_range_end=5/29，first_breakdown_at=6/2。人工4/7～6/2／39筆、6/3外及5/13局部代表已答，不能重問、刪6/2或稱25筆等於39筆。
3.B67→68→70→72→74→76→77為同尺度來源轉折ID前綴延長。保留全部歷史，但明示發展版本、跨尺度同幾何及真正局部不同；不將89個候選當89獨立型態或多尺度當獨立成功票。
4.B77的successor_after_breakdown_ids有32個，只是同段且晚於破底的全部後來箱，不是直接下一箱或因果承接。B44／B80無parent不代表完全無關係，但純幾何包含無法表達人工大帶意義。
5.B88從2025-11-19～2026-07-14，9/1確認，含1/27=26.95但未完成六月後整體歸屬。1/27轉折3/4／3/20才確認，不能倒灌已知。10/12上越、13跌回、14再越、15再跌回、16再越保留。
6.最大後續跌幅所用觀察期間不同，僅明示區間與資格，不自行新增正式衰減／重要性權重。

本次工程目標是透明可追溯診斷：輸出被拒／未選串的原因及數值餘量、日期各語義、既有候選精確來源前綴版本鏈與跨尺度同幾何關係；將廣義時間先後資格與直接承接未知分開，呈現觀察長度。不得將診斷硬接成正式箱歸屬、合併或選關門檻。舊核心／JSON原結果及既有頁面保留，新的診斷可加獨立版本或附層，UI只讀數值。

適量測試同源前綴、追加未來不回寫、關係不成循環／不獨立計票、被拒原因可重現、缺資料與多尺度不同確認時點；原完整策略回歸無關不重做。若改HTML，實核來源與SHA、必要真實HTTP，不沿舊115當新通過。UI有可放大的真實差異圖，不以說明或箱數替代主要壓力辨識完成。

primary_pressure_id仍null；正式區界／量口徑／增量／強度衰減／生命階段未知。Raw公司行動／五年Adjusted／歷史公布可得／資料缺口／Darvas正文／SQLite未知保持；不是模型訓練、準確率、全市場或交易認可。新Android NOT_TESTED_NEW_BUILD，file://不重試不繞過，不索舊圖JSON或重做舊按鈕QA。

一般可逆工作直接做，不改main、原引擎策略／庫／歷史／舊頁／案例及手機證據，不部署付費交易發訊息或啟動子代理。完成後源碼、實測、失敗及新接續入口保存同分支、逐檔GitHub回讀；未測不標完成。結束列實際完成／未完成、入口、最新提交及下一步Work或Codex；換模式附完整可貼指令。
