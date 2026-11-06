# M-R2 原里程碑續作｜有限研究日簿0.1（實作前凍結）

不改原BLOCKED證據；新結果另存本目錄continuation。只加入純日簿組裝／既有事件後續觀察，不改graph_core0.2、F-01、來源門檻、M-R1等待次數／參照、資金或策略。

## 摘要可用範圍評估

既有`rotation_research.store.Journal`可保存未合格研究結果，沒有要求每一項研究觀察都先取得原始回應。`capital_research.evidence.from_saved_layers`的available_at檢查與`real_source_gate`屬資金／正式來源路徑，本輪不呼叫、不降低。FinMind個股intake仍沿原完整資料／指紋／日期基底檢查。

使用者本輪已明確授權把總監讀回M-R1原件的兩日四份摘要作有限回顧研究輸入。新摘要角色固定`DIRECTOR_READBACK_RESEARCH_SUMMARY`，必有日期、市場、必需欄位、原網址與**reported**原件SHA、摘要提供時間；original_read_by_codex=false、official_reverification=NOT_PERFORMED、historical_available_at=UNKNOWN、strict_common_stock_universe=UNKNOWN、redistribution_permission=UNKNOWN。SHA只是總監聲明，不拿摘要自己的hash冒原件SHA讀回。這是另一種低資格的研究觀察，不進原正式來源／帳務閘門。

因此可做研究摘要連結，真實接線資格為**PARTIAL**；不是BLOCKED，也不是來源原件認證PASS。來源角色／研究完成與正式資格分開；全部正式false、主壓力null與真實來源拒算保持。不能靠改角色／synthetic標記放寬真實資料資格。

## 輸入及不變量

`graph-market-diary-input/0.1`明示原graph input＋完整0.2保存結果／來源角色、同日TWSE與TPEX摘要、可選的外部研究window_dates。純組裝不分析／重播／IO；外層重用原Journal保存讀回。結果`graph-market-research-diary/0.1`。

原結果schema、result_id／前綴／來源／基底／錨點、原事件時點及F-01皆校驗，不能只靠事件ID。只用<=as_of的完整資料與當日市場，不選最近日期、不補缺值。每個日行保留原完整圖形結果；原pivot ID／事件body原樣保存。原box path沒有事件ID時original_event_id=null，另有明示的derived diary key與原box／path索引，不冒稱新增原事件ID；原confirmed_at缺少仍null，不自造確認。

當日新確認pivot只取confirmed_at=當日；箱路徑事件只取原date=當日。已知候選／不可比／pending狀態保留原結果。原每日entry不可用後來行情／市場回寫；後續觀察另列followup_updates/evaluated_at，整體來源完整性／外層result_id與每日已知內容分開。

歷史市場摘要只在回顧軸可連結，historical_signal_eligible永遠false；received_at是現在交付時間，不回填歷史available_at。少欄、錯日期／來源／基底／schema／原事件被改、偽稱原件已讀或正式資格升級明確拒絕。原來源完整性只是保存一致性，不是來源真偽認證。

## 後續觀察

不推定M-R1窗長，不設比例／天數。若有window_dates，須外部明示有序不重複、晚於原事件、附來源及`EXPLICIT_RESEARCH_SETTING_NOT_STRATEGY`。完整只指供應研究窗，非完整交易曆認證。缺預期日／缺價／跨中斷拒判，未知不補零。

只有原箱路徑`CLOSE_ABOVE_RESEARCH_RANGE`與同原箱後來既有`FAILED_UP_RETURN_IN_RANGE`／`FAILED_UP_AND_CROSSED_BELOW_RANGE`可做本版明示失守觀察。不是新增判圖條件，不另定跌幅或價位。pivot HIGH本身沒有獲批的突破／失守定義，故不自動套箱失敗規則。

輸出區分`IMMATURE`、`KNOWN_EARLY_FAILURE`、`FAILURE_IN_COMPLETE_WINDOW`、`NO_FAILURE_IN_COMPLETE_WINDOW`、`UNKNOWN`，並另列maturity／known_failure／reason。已知早期失守在窗口未滿即揭露；完整窗未見失守不稱成功／獲利。跨基底後不再比較，但中斷前已見失守仍保留known_failure與原事件。未提供窗或失守定義時不判完整結果；新pivot尚無後續觀察可標IMMATURE，失守評估仍UNKNOWN。缺資料不靠窗口到期變成功。

7/21、7/22真實案例不另填window，7/22HIGH保持occurred=7/21、first_observed=confirmed=7/22。2408無可核原件仍不接入。全市場比率／真實淨績效始終null／拒算，市場觀察不產生交易指令。

## 保存與驗收

完整總監市場摘要、FinMind行情、圖形結果及日簿只留Git外。公開限程式、合成fixture／actual、原碼指紋及非行情白名單摘要；不發布本輪市場數字／報表SHA聲明或可還原行情的事件ID／價位。原blocked log／manifest不覆寫。

先凍結輸入／預期，再執行定向正反例與必要回歸。覆蓋兩日日事件時序、未來隔離、角色／來源／日期錯配、缺欄、F-01、未成熟／早失守／完整窗兩種結果／缺資料、母體與資格拒算、Journal同內容／衝突及READ不重算。不重跑舊全套／81日／敏感度，不抓任何新行情或Library入口。一次完成必要修正、自審、正常保存讀回，達成本輪有限研究接線即停。
