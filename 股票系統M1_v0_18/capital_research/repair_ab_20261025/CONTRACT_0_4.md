# 隔離研究 A/B 修復契約 0.4

0.3 原樣快照固定在 `34b5dfa22b77cfe5c85a818e156389d5d0f9a444`，已正常推送並經 GitHub 讀回。其歷史「未提交」敘述、原 manifest、快照、before/after 和 log 原樣保留。本文件及新證據另存，不把舊保存結果升級或重算。

新輸出為 capital-decision/0.4、capital-execution/0.4、capital-comparison/0.4、capital-account-checkpoint/0.3。傳輸 input 外殼不變；舊輸出仍可 READ，不能自動升級成新 checkpoint。本輪沒有改正式策略、圖形規則、歷史資料 schema、trend 或 action_ledger。

## A：新資金事實必屬本股

core 為每股建立當時已知、且通過來源／基底／調整版本檢查的 evidence map，僅把該 map 傳給 entry_review。跨股全域表仍用於原有事實 ID 衝突檢查，不能作另一股票的加碼資格來源。

entry_review 再檢查引用 ID 必須出現在該 asset 自有 evidence，且來源、價格基底、調整版本逐欄相符。即使兩股使用同一 generic source 或同一基底字串，也不能從外部 map 借用另一股未歸屬本股的事實。缺事實、未可知、未合格、過期或撤銷維持拒絕。

資產 JSON 物件排列不能改變本次 A 反例或正例的決策。有效舊事實仍可由當期 review 引用原 ID，不強迫成為新事件；原 formation/event/volume token 去重保持。目標未增加卻送 BUY、拆單總量超過目標差額，仍由既有 execution 合計數量及方向防線拒絕。

本修復不提供跨輪不可變事實／撤銷登錄。若輸入另行改寫來源有效期或丟棄已知撤銷，不能冒稱已全面辨識「換名復活」；此為未覆蓋邊界，非本輪擴充。

## B：取消前活單區間不能消失

本 adapter 只有明示日終 checkpoint，沒有不中斷的舊單盤中完整重播。若 checkpoint 尚有活單，且從其日終到取消 review 已跨入另一個原 ledger 明示為 trading 的日期，account_at_checkpoint 必須拒絕：

`ACTIVE_ORDER_GAP_CONTINUATION_NOT_IMPLEMENTED`

省略較早 tape 不證明舊單沒有成交，也不解除此拒絕。不得先把舊單預留歸零、忽略可能成交，再用舊帳建立新委託。要支援該區間，後續需有完整且可回查的較晚帳務／委託 checkpoint；本版沒有自動補造。

日期比較採 checkpoint 的明示時區，並使用原 ledger 完整 calendar；不推真實開盤時間、券商取消確認、T+2 或新的固定檢討天數。若中間日期全部明示非交易日，本限制不因經過日數而觸發。保守拒絕包含已跨入 trading 日期但未證明實際開盤／成交的情形，這是表示能力界線，不是交易策略門檻。

原 checkpoint 已記錄到期／取消的單不屬活單，可依原規則接續；僅有「未來會到期」但尚無完整後續 checkpoint，不等於中途無成交。原同日收盤後 review、下一交易日才觀察的正例保持。被允許的續接會在 continuity 保存 cancellation_effective_at，舊單 state 及 execution_events 保存相同 cancelled_at／取消事件。

取消只釋放該委託預留，一般 reserved_cash=100 仍由原帳承接。原始 opening、本金、完整 fills、現金／股份權利、應收應付與剩餘量仍只有 action_ledger 入帳。本輪沒有第二套會計或無縫外部既有單引擎。

## 新證據與版本比較

before、after 各保存七個定向合成 job 的 input、預先保存的 expected、actual、summary 及來源指紋。輸入 JSON 保留資產順序，不先排序而抹掉 A 的反例。after 的 B 前身以新引擎從同一 opening／市場／成交 prefix 明示重新產生；fixtures.rebind 逐項要求 row、accepted_fills、origin_initial_capital、general_reserved_cash 與舊保存前綴完全相同。只有版本及衍生身分重新綁定，不把 0.3 checkpoint 靜默升級，也不改 oracle。

capture／verify 只能輸出至新目錄或 create-only 新檔。舊0.2／0.3 builder、verify 與大批序列為其封存版本，不是在新 source 上重寫舊結果的入口。

全部正式資格及授權 false、主壓力未知 null，70拒算／2不足／其中8換股影響未支援／合格真實總淨0保持。R2/F、信用、期初應付、外部既有單不中斷完整重播、無來源限售解除、真實日終／交割認證及實現曝險配對仍未實作。無真實 producer、資格重算、市場六方案、UI／Android 或樣本外執行；合成案例不構成市場績效或策略勝負。
