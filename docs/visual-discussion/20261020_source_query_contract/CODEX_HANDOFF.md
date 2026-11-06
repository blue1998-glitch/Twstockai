請接續股票系統M1，實作「既有診斷中的單一來源反查」，嚴格限於已保存來源關係與明示路徑查詢，不實作自動大帶歸屬或合併。

儲存庫：blue1998-glitch/Twstockai。分支：dev/m1-v018-chart-annotations。本輪已核起點a30b62f050c8ca55668f54f7a0bd3e46955d6bda；工程交接db000b9a7a09c2bbc693e9d2094482a5edd6b867；數值成品2d9c9aad4b88b53d9552e479a3f625377f2b7161；原真實圖fff47915523fab8c8de8279de8bbb7a26b05647b。本輪最新研究提交見docs/visual-discussion/20261020_source_query_contract/GITHUB_READBACK.json；先確認分支包含全部指定提交。若有更新先讀最新交接保留全部後續成果，不用main或舊ZIP覆蓋。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節。全文讀docs/visual-discussion/20261020_source_query_contract/README.md、SOURCE_QUERY_CONTRACT.md、本檔、path-audit.json、provenance.json與GITHUB_READBACK.json。再讀20261020_structure_membership_work_review/README.md、user-decision.json、source-membership-audit.json及前輪更正USER_CORRECTION.md。沿用deliveries/m1-v019-reaction-facts-20261020/README／WORK_HANDOFF／收據及reaction_facts README／validation驗收／selection，完整reaction_facts契約與原facts、pressure_update_evidence/user-decision.json。按需讀reaction-facts.json，不重讀101圖／0.4.3或舊手機驗收。

本輪Work已全文讀graph_diagnostics/README.md、build.py、diagnose.py、viewer.js，原診斷已有完整同尺度來源序列、箱source_turn_ids、版本及同幾何關係。先在實際完整checkout依AGENTS實跑準備／核固定來源，保留所有差異，再搜尋已有等價查詢函式及adapter。重用等價能力，不另造第二套核心／診斷／反應事實／圖表。本輪Work沒有完整checkout bootstrap成功收據，不能冒用別環境準備。

工作範圍依SOURCE_QUERY_CONTRACT：在既有graph_diagnostics內提供純數值來源反查（可source_query.py），輸入已核原core result及明示pivot IDs／同尺度同段的from/to路徑／實際selected_at。查所有原箱引用及序位、完整同來源座標別名及各自確認、全部有序中間轉折；不裁箱、不自動跳尺度、不隱式猜終點、不遞迴吸納歷史。錯誤ID、混合前綴基底指紋、未確認、倒序或跨尺度段明確拒絕。重用原精確數值／fingerprint／封包來源驗證，不呼叫diagnose或原辨識指標重算來查詢。comparison內diagnostics僅摘要，不能假裝完整diagnostic_id驗證。可加必要CLI／adapter及精確小JSON，不加產品UI，不重做主圖或reaction_facts，無需因此重跑瀏覽器／Android。

真實fixture：A原6/5高39.25的3%來源應反查B16／B17／B18，三箱六月前來源與40.25均保留但不成為人工整體成員。A到11/28原3%高的9點路徑全保留，末高35.50高於前高34.15；10/24低31.35與11/28高35.50的3%／6%ID及確認不同，完整source_dates相同，列對照不合併。全部原3%／segment0序列有119點、2021-11-29～2026-10-13；9點路徑前33後77，證相鄰路徑不是整體起訖規則。數字／日期／價位／ID僅fixtures，不進生產常數或選關條件。原89版本／84幾何非獨立型態、B77／2022B6價域重疊反例保持。

必要測試按契約實跑：真實來源／所有原箱引用與有序完整路徑、同價多來源及source_dates差異／不同確認、無效／未確認／混合來源／跨尺度段／倒序拒絕、原前綴在追加或改未來下查詢不變、純函式確定性及輸入不可變、原core／MACD／reaction／圖表／所有策略參數與來源案例保存。重用既有等價測試，不湊數；清楚記錄真正執行、失敗與修正。新數值功能不用新瀏覽器驗收冒充通過；若意外修改UI先縮回範圍，必要變更另實測。產物用新output葉目錄，不覆寫舊包。

生產查詢目前NOT_IMPLEMENTED、契約測試NOT_RUN；Work只實跑研究probe一次，核119原點、9點子串及同座標source_dates、來源bytes不變；沒有22項測試重跑、核心／MACD／reaction重算、新ZIP、bootstrap、瀏覽器或Android。Android NOT_TESTED_NEW_BUILD；file://不重試不繞過。工程完亦不等自動主壓力辨識完成，必須回Work用可查來源研究正式歸屬。

已確認不重問：整體可包含不同形態區段、不要求整體符合局部橫箱同條件；局部與整體分判；本例未挑戰左側舊帶高點前不因低位整理先降重要性。月份、39筆、5/13、6/3、1/27等舊案例不重問。未批准正式成員／區界／代表／合併、解除、衰減、量權重或買賣規則。primary_pressure_id=null；不把39.25／35.50／35.45／40.25指定整體代表。

五月反覆站回跌回、紅K但較前收跌，以及十月日高過而收未過、低相等、正MACD下跌回與全部反覆路徑保持。相等不補過破，日OHLC不證日內順序。原值可知／原確認與後來實際選取分開；historical_signal_eligible=false。原拒絕餘量−2.4800／−0.7825、來源末轉折／確認／研究離箱／人工終點分開，49轉換非訊號、廣義後來非直接承接、不同窗不排名保持。正式區界代表／增量／衰減重要性／合併直接承接／生命階段及Raw公司行動／五年Adjusted／歷史可得／九待核日期／非窮盡日曆／Darvas／SQLite未知，核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED保持。

保留原核心參數策略／庫／歷史／舊頁／案例證據及main；不調參硬編答案、不新增自動選關或合併／正式解除／量權重／買賣門檻，不部署付費交易訊息，不啟動子代理。若需新核心策略先回Work以真實圖討論，不自行補答案。所有新增及修改保存同分支，逐檔GitHub回讀原文／binary／ZIP（若有）與收據；未讀未測未執行不得標完成。結束附最新已核提交、入口、完成／未完成、實際驗證與完整回Work續接指令。
