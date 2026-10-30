# 新批部分成交後續播：交付報告

## 實際交付

基線5c6d04b487375f85f611ef34cc2fdbdc0037e583；開始時本地／遠端一致，tracked／index／untracked皆0。原唯一Codex於原/workspace/Twstockai及dev/m1-v018-chart-annotations完成。本輪只新增有限合成使用案例／證據／必要測試，**所有產品模組未改**。

已保存前輪checkpoint、最新新批B20完整job與明示已核checked_action只READ。本輪另建外生容量模型，使用既有1/9容量7 tape，價格／市場狀態／available_at／來源／基底／交割日／原日曆均不變，不把舊全成actual改成部分成交。先凍結CONTRACT、full root、prefix外部請求、path、獨立手算預期及反例規格，再由原cash_action_execution.execute生成新prefix。完整root的一次執行控制亦使用同一原引擎，不另建帳本或回放系統。

## 帳務與委託結果

原1/8已結清帳已有B7/C2，現金858.86、一般reserve100、現金權利80及C2股份權利，原始本金1180。舊explicit-order剩13已到期，新獨立B-step2核准的second-B-buy20在1/9只成交7。新fill為second-B-buy-fill-1，原fill explicit-order-fill-0保持；合計B14，未用同一觸發重開新批。

新7成本7×20.02＋原最低費1＝141.14；1/9已結仍858.86、應付141.14、嚴格可用717.72，一般reserve100另列；新單剩13、預留261.65039。1/10使用原已保存非交易日close，應付／預留均未提前消失。1/12只結一次141.14，原現金權利80與股份權利C2各到位一次，最終現金797.72、B14/C4、應付0。新單剩13在原1/12 12:00期限到期，預留釋放0；舊到期13始終保持原狀，沒有重下或復活。

原本金1180不是當期淨值，不重開。每日均獨立核對現金＋應收－應付＋實股估值＋待交股份權利＝原ledger淨值；終點1177.72只是合成費用對帳，不是市場成長或策略績效。

## 真正續接與等價驗證

- root_job.continuation保留的是**該新批起點的1/8完整前身**；外層resume checkpoint才是1/9或1/10目前水位。兩者不能互換，不能把目前應付款塞回新批的假期初帳。
- 新批prefix含前後兩次決策、12個歷史token、原fills／closed order與新部分單。續播的decision_records、latest／common account、fact_sources、重評紀錄、tokens、原order_history及opening_unavailable_shares均不變。此案例重評attempts為空，不冒已新增非空0.9重評／完整分叉驗證。
- 1/9→1/12直接續播，及1/9→1/10→1/12兩段續播，完整execution及checkpoint都等於同root的一次執行控制。所有共同明示觀察（原1/9三點）及全部ledger每日列皆一致，中途1/10列也與一次執行相同，並非只看終點。
- 三份正例的尾段觀察數皆0，因明示完整path在1/9後無新觀察；尾段確實由carry狀態處理交割及到期，沒有新增decision／order／fill／token。歷史重建與尾段處理數分列，不能冒整個RUN無引擎。
- 內層execution.new_fill_ids依原root累計仍含新7；外層new_fill_ids_this_segment空。原單數量、期限／限價、一般reserve、全部權利與前身回連均保持。

## 反例與測試

五個先凍結反例均依原機制拒絕，tail_processing_started=false、尾段0、execution/checkpoint=null：

| 反例 | 保存拒絕原因 |
|---|---|
| 把expected_latest改成前一輪ID | EXACT_LATEST_PREDECESSOR_REQUIRED |
| 刪root的完整continuation | Opening ledger/cutoff mismatch |
| 容量500路徑配部分B7 checkpoint | PREFIX_EXECUTION_MISMATCH |
| checkpoint重複fill | Execution fingerprint conflict |
| 漏1/12空日完整性證明 | COMPLETE_SESSION_COVERAGE_REQUIRED |

最終4個唯一測試方法首次全過，見tests-final.log；不累加歷史4／9等PASS，也不把三個正例／五個反例當八個測試或市場樣本。凍結input／expected、原件、產品source、輸入不變與保存JSON讀回均核對。沒有失敗、oracle更改或產品修補。原已保存續播／兩輪producer／舊suite／quantity生成與回放協調器均未重跑。

數值環境、未來隔離及未變入口的機制證據沿原source重用，本輪不冒新增完整矩陣。無新行情／日曆、真實producer、市場回放、資格重算、UI/Android或樣本外；只有新的明示合成prefix、同root一次執行控制及本輪續播請求。

## 限制與下一步

本例驗到新批部分成交後的**交割及剩餘到期**，沒有1/9之後新的成交觀察，不宣稱剩13再成交。1/12無機會宣告是明示合成模型假設，不是市場認證；缺該宣告須停止。沒有新策略、比例或自動選擇，不能把新股數當使用者正式規則。真實1101期初cash_claims UNKNOWN、70拒算／2不足／其中8換股影響未支援／真實總淨合格0、正式false／primary_pressure_id=null、來源0.10全部parents、正式action_resolution0.4與圖形人工保持。

任意外部單、未知期初款、限售解除、來源認證、尾段新重評／新決策、R2/F及完整分叉仍不支援。Work／Astra／第一工作區救援原件未取得未讀，不要求使用者搬檔或私人資料，不推定890檔存亡。

這項接續已結清，不再為相同範圍重建入口或新增READ工具。若要決定何時續抱、加碼、減少或退出，仍需Work與使用者研究觸發、期間及風險取捨；不能由Codex自行定規則。本輪一般工程與保存不需人工操作，亦不要求Work例行驗收。
