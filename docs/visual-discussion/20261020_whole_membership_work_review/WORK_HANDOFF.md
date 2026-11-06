請接續股票系統M1，同Work使用已完成來源反查研究正式整體歸屬，先處理新的共享交界來源角色問題，不重做查詢、圖表或reaction_facts。

儲存庫blue1998-glitch/Twstockai；分支dev/m1-v018-chart-annotations。本輪已核起點e0bd48c9245c877fda8ebca5598f69ff346a99cb；來源反查成品e45d972406cc6a4ef1a9babf1ba9865d97073096；原真實圖fff47915523fab8c8de8279de8bbb7a26b05647b。先確認最新包含以上提交；若更新先讀最新交接保留全部成果，不用main或舊ZIP覆蓋。不能讀GitHub明說未取得，不假設已讀。本輪研究提交見docs/visual-discussion/20261020_whole_membership_work_review/GITHUB_READBACK.json，收據本身另回讀，最新以實際HEAD為準。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節。全文讀本輪README.md、本檔、pending-decision.json、junction-evidence.json、read-provenance.json、visual-observation-status.json及GITHUB_READBACK.json。沿讀deliveries/m1-v019-source-query-20261020/README.md、WORK_HANDOFF.md與GITHUB_READBACK.json；再讀股票系統M1_v0_18/graph_diagnostics/SOURCE_QUERY.md、source_query_validation_20261020/驗收報告.md、verification.json、source_query_examples/request.json及source_query_generated/source-query.json。沿讀原SOURCE_QUERY_CONTRACT、structure_membership_work_review README／user-decision與reaction_pressure_work_review/USER_CORRECTION.md。原reaction_facts契約／原facts及既有反例保持，不重讀101圖／0.4.3／舊手機驗收。

本輪新問題PENDING_USER_ADJUDICATION：將來正式區段是否允許同一實際K線低點被相鄰區段分別引用、各記不同角色，而不強迫只能歸一邊，也不因共用就合併？原圖綠色B77來源框左側起點的2023-10-24低31.35是具體案例：原3%記錄為B19來源串末點，原6%同座標記錄為B77來源串首點。助手建議允許角色並存、保持原ID／原箱身分；尚未獲答。若使用者接續回答，先解析範圍；認同也只確認角色可非互斥，不批准本例正式分段／成員／區界代表／合併／直接承接。

不要把此問當已答的「整體可含不同形態」「局部整體分判」或「同座標不合併」重問；新的核心點是未來正式區段來源角色是否必須排他。B19末來源不是正式整箱終點，B77首來源不是已批准大帶起點。3%低點11/2確認／B19亦11/2確認；6%低點11/20確認／完整B77到2025-03-24才確認。不能回填2023已知整個B77或正式整體歸屬。

本輪用新JSON核17原轉折完整記錄、8原箱回傳欄位與原comparison全等，精確核30584 bytes／SHA4a43a8c0f03bbffacb86306f064b7c807a7a83bdaf7e737bc76cd654a2c1dbb0。新JSON只查3個明示3%點，6%只是座標對照、不遞迴反查；B77首來源由原已保存core另讀，不是新JSON漏檢或遞迴展開。工具不需重做。原query selected_at為2026-10-20T07:30:12.393327+00:00，歷史選取null／historical_signal_eligible=false。

A仍反查B16／B17／B18，六月前40.25等全部原來源保持，但不因引用就納入人工整體或指定代表。9點路徑末高35.50較前高34.15高1.35；與更早9/14高35.50卻相等、差0.00，不補突破。119點／前33後77只作背景，路徑相鄰／價格重疊／同座標均不作自動成員或全歷史串接條件，原ID與確認不合併、不投票、不跨尺度冒充同尺度路徑。

三個已確認概念不重問：異質形態整體不必過局部橫箱同條件；局部整體分判；本例未挑戰左側舊帶高點前不因低位整理先降其重要性。月份、39筆、5/13、6/3、1/27等舊案例不重問。不擅定39.25／35.50／35.45／40.25為正式代表。五月反覆站回／跌回、紅K但較前收跌，以及十月日高過而收未過、低相等、正MACD跌回等反例全部保留；相等不補過破、日OHLC不證日內順序。

本輪成功取得並讀全部指定GitHub新成品與交接；原圖PNG亦從GitHub逐byte核等，沿用舊真實圖。新標註截圖未完成：先有觀察腳本SHA預期字串誤植，守衛在啟動前拒絕；改成已核SHA後，前輪Chromium執行檔已消失、啟動失敗；現有本機瀏覽器查找無結果，未安裝、不走file://。無新成功瀏覽器／Android驗收或PNG，不能沿舊圖冒稱新跑。不是產品查詢缺陷，不交Codex重做工具。Android NOT_TESTED_NEW_BUILD；file://不重試不繞過。

本輪只有新JSON下載核SHA／欄位與來源角色審閱、Decimal原值比較及舊圖再取回核對；未執行source_query／adapter／CLI、bootstrap、原辨識／MACD／reaction、新ZIP、14或舊測試。14新測試PASS／27檔GitHub相符、fixture隔離初敗修正是已讀上一輪工程紀錄，不當本輪重跑。保留原拒絕餘量−2.4800／−0.7825、來源末轉折／確認／研究離箱／人工終點語義，49轉換非訊號、89版本84幾何非獨立型態、廣義後來非直接承接、不同窗不排名。

primary_pressure_id=null；正式成員、區界代表、增量、量權重、衰減重要性、合併直接承接、解除及生命階段未知。Raw公司行動、五年Adjusted、歷史可得、九待核非窮盡日曆、Darvas、SQLite未知；核心NOT_ESTABLISHED／分類NOT_VALIDATED／行動NOT_EVALUATED。新核心歧義用具體原真實圖討論，已定規則或可重現工程缺陷才交Codex。

保留原核心參數策略／庫／歷史／舊頁／案例證據及main。不調參硬編答案，不實作未定自動合併或主壓力選取，不新增正式解除／量權重／買賣門檻，不部署付費交易訊息或啟動子代理。成果及實際成功／失敗證據保存同分支並逐檔GitHub回讀；未讀未測未執行不得標完成。結束提供最新已核提交、入口、完成／未完成及完整續接指令，說明下一步仍Work或何時可轉Codex。
