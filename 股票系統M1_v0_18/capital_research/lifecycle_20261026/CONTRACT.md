# 原批次生命週期唯讀摘要 0.1

基線3b025c6a94a65fdb3cd1f0afa023dbaacb5d1374。只讀既有quantity_replay/0.1及conditional_quantity_review/0.1保存JSON，不呼叫／匯入決策、候選、成交、帳務、checkpoint重建或來源資格producer。核心無檔案／網路IO；CLI只開輸入檔讀取並輸出stdout，不寫檔、補資料、回算或隱式升版。

## 入口與範圍

`lifecycle.summarize_saved(saved)`接受上述完整保存wrapper，輸出`capital-batch-lifecycle/0.1`；不接受任意as_of、替代帳戶、外部補價或計算參數。歷史不同schema明確UNREADABLE，不遷移。新摘要不等新的交易資格／策略驗收。

原研究提案按原decision_id／candidate_id列一次，列出共享該提案的order IDs；逐單生命週期以原order ID區分，同一張單重評不新建批次，下一輪新order仍另列。拆單共用提案，不把每張單的數量當成各自可重用的整筆預算。核准僅指保存的合成研究提案及其已記錄原單數量；正式授權永遠false。找不到原提案綁定時approval=UNKNOWN，不能由目前持股或active_decision推導。

## 摘要內容

- 來源schema、保存status、observed_until、日終as_of／available_at、來源完整性ID及JSON pointer；停止結果中的舊帳明標HISTORICAL_BEFORE_STOP，不當本輪成功結果。沒有可讀執行紀錄時NO_SAVED_EXECUTION，所有金額／數量unknown不補零。
- 每張原單：原提案身分／目標、原單上限、累計實際成交、仍活著的remaining、已取消／到期未成交量、原reserved_cash、requires_reassessment、active／origin decision及保存事件。原remaining是未成交量，終止後不能當仍可買。只對明示完整整股量做加總與守恆檢查；不是會計或風險重算。
- 每筆fill：原價格、費用、稅、股數、交易日及明示settlement_date。逐筆交割只用保存journal的PURCHASE_SETTLED／CASH_RECEIVED(SALE)對應fill_id／claim_id確認；未到保存日且無結清紀錄為PENDING_SAVED_SCHEDULE；到日但沒有逐筆結清證明保持UNKNOWN，不憑日期宣稱已結清。沒有逐筆待付金額就null，不按price×shares重建。帳戶應付另照原row列出，不能重複分攤到每單。
- 當期帳戶與各保存snapshot：現金、嚴格可用額、一般reserve、應收應付、實股、cash／share權利、opening不可賣量、origin資本、latest及完整reviewed tokens原樣列一次。逐單預留另列但不加回現金，不重設本金，不產生可用額度建議。
- 重評：decision_at、data_cutoff、observed_at、ACCEPTED／REJECTED、原decision_id／checkpoint_id／request指紋、理由、當期資格與限制衝突。只摘保存decision的當期結果，不用完整fact_sources內未來尾段重新判定。有效舊事實與新trigger仍由原結果表達，不重新分析。

## 防護與未知

只用標準函式庫驗原JSON指紋、已保存snapshot之間的原order／fill／decision／token延續及checkpoint／原ledger row欄位一致；不重新執行任何機制。這是結構與保存一致性檢查，不認證來源真偽、不保證任意分叉或中途資金絕無重用。

缺必要欄位、指紋不符、重複fill、fill↔order不符、量不守恆、跨snapshot原單／fill消失或變更、checkpoint與保存execution不符：UNREADABLE且不輸出可誤用的部分金額／數量。可選的理由／逐筆交割證明缺少則明列UNKNOWN及限制，不補零、不猜成交時刻或退資權利。未辨識order status亦UNREADABLE，不能當活單或已取消。

原帳、原權利、reserve、latest、tokens和舊actual／oracle／log不改。本輪證據以原件路徑＋SHA及明示JSON變體指定輸入，重用保存原件，不複製／重跑舊producer；新input specification／expected在實作前凍結。必要測試包括舊單續用／新單區分、部分成交／待交割、取消／到期、拒絕重評、未知及損壞、停止結果、輸入不變，以及禁止引擎import與CLI不寫檔。未來價格的既有保存三分支只讀比較，不重跑。

所有正式資格false、主壓力null、1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0保持。R2/F、信用、期初應付及外部活單等原未支援能力不擴張。無UI、真實producer、市場績效、樣本外、新來源或私人文件。Astra與第一工作區救援原件仍未取得／未讀。
