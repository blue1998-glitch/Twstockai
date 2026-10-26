# 跨輪事實內容保全研究契約0.5（本地未提交）

基線 `4339a146d22dd849a6131a8c13f08f2e56145a2f`。本輪只授權定向重現／修復與可審查差異，沒有commit/push授權。舊0.2／0.3／0.4、來源、before／after、log及快照均原樣保留。新輸出capital-decision/0.5、capital-execution/0.5、capital-comparison/0.5；checkpoint為capital-account-checkpoint/0.4。輸入傳輸外殼不變；舊結果READ不重算、不隱式遷移。

## 身分與內容

新純模組fact_lineage不含檔案、網路或會計IO。事實身分範圍為code、source_id、basis_id、adjustment_version、kind及id。EVIDENCE必須有非空id；缺失明確FACT_IDENTITY_REQUIRED。ENTRY／REFERENCE沒有來源id時，只以原available_at及occurred_at建立同股同基底的明示研究快照身分，並非原始來源永久ID或真實認證。

歷史保存當時可知的fact、內容指紋、observed_at、原身分／別名、接受或拒絕原因與目前仍有效的原件。事實本體（含事件／形成點／量柱、內容、類型、立場及原時點）不得由同ID靜默改寫；來源更正處理仍FACT_CONTENT_REWRITE_NOT_IMPLEMENTED／FACT_CORRECTION_NOT_IMPLEMENTED。可增加當時才可知的有效期資料或收緊限制，但已知有限valid_until不能刪成null或延後，valid_from不能改寫，已知撤銷不能刪除或覆蓋。

資格拒絕只限制相關新增資金及新觸發，沒有永久封鎖該股票。原件仍有效時，恢復其精確已接受內容可解除一次被拒提案的標記；原件若後來過期／撤銷，不能藉恢復舊bytes復活。真正不同、當時可知且有當期review的新事實可以競爭，舊失效紀錄不刪。

## 明示別名與未知

`fact_link`為capital-fact-alias/0.1，包含code、source_id、basis_id、adjustment_version、target_id、target_content_id、available_at、source_ids。必須指向同股／同基底／同kind的已保存內容指紋，且當時已可知。別名只承接原事實，不改造成獨立事件，也不解除其失效。

沒有連結而在同範圍出現完全相同本體的新ID，列FACT_RENAME_LINK_REQUIRED／未知，不能直接當新事實。錯股票、錯來源基底、未知target或內容指紋不符皆拒絕資格。無法辨識的連結、已建立另一身分後才要求合併的別名，保持UNKNOWN／LATE_ALIAS_MERGE_NOT_IMPLEMENTED，不猜測來源關係。

不能僅依共用量柱、形成點或相依token合併真實事實。相依去重仍由原evidence_tokens處理；不同事實可以共用量柱，但不因此算兩個獨立觸發。有效舊事實與合法別名可由當期review使用，沒有被強制改成新事件或固定有效天數。

## 時點與連續帳

execution的`fact_sources`按每個decision_id保留完整明示來源宣告（含尚未知的未來撤銷），只屬完整性資料。numeric decision的`fact_history`只包含當時可知投影，schema=capital-fact-history/0.1；未來撤銷內容不進早期history／decision_id。knowledge事件必等occurred_at與available_at均到達；發生但尚未公布不能提前取消。

resume只從已驗checkpoint的完整fact_sources／decision_records取歷史，不信任輸入自報的history取代前身。每次新decision的history可從此前全部宣告重建；checkpoint再逐筆比對所有decision的版本、指紋、截止與重建history。缺一輪宣告、刪改已知原件，即使重算外層execution指紋也不能與原decision history相符。中間一輪省略事實不清空早期紀錄。

當先前宣告的撤銷後來可知，standing BUY即使本輪review省略其欄位，仍使用完整歷史取消。每個市場觀察都在成交前檢查；沒有後續市場tape時，明示observed_until亦處理當時已知失效並保存取消事件。取消事件at保存首個當時已知失效時間，observed_at另存實際處理觀察／watermark；較早到期或同時到期者維持EXPIRED，不被較晚撤銷改寫。這是合成引擎的觀察／watermark處理，不保證券商即時取消或能撤回已成交部位。先前已成交者不因較晚撤銷而回寫刪除。

checkpoint.state的fact_history只投影到through_at；完整未來宣告仍留在execution完整性資料。原origin／latest、帳戶／fill／order／token檢查保持。現金、權利、應收應付、持股、預留及原始資本仍只由原action_ledger入帳；本模組不是第二套會計。

## 能力界線

這是明示合成來源的連續性查核，不是密碼學簽章、通用來源認證或任意造假的偵測器。若所有來源、永久身分、事件及時點都被一起偽造，不能宣稱已識別其實際同一性。匿名ENTRY／REFERENCE只保護同一宣告快照，不認證改時點後仍屬原事實。合法來源更正／撤銷撤銷及複雜身份合併沒有自動批准流程；不支援時明確拒絕／未實作，不從新decision_id推導授權。

本輪無真實producer、來源資格重算、全市場／六方案、UI／Android、樣本外、R2/F或完整外部既有單重播。正式資格與授權全部false、主壓力null、70拒算／2不足／其中8換股影響未支援／真實總淨合格0保持；不補未知、不放寬來源拒算，不改正式策略、圖形、P0-3/P0-4或人工模式。
