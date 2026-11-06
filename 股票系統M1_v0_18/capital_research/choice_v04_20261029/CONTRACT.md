# 保存0.4候選的明示研究選擇｜實作前契約

基線9d7931c4dad658044385751533736f216423a91f，原工作區／分支／唯一Codex。只接已保存候選，不重新generate／decide／resume／replay、不入帳、建單或成交，不發明策略／N／比例／門檻。舊choice-input／choice 0.1及其0.2 generation包裝保持相容，不改舊原件。

## 明示來源與版本

choice-input/0.2沿既有exact欄位schema、synthetic、saved_result、source_binding、selection、recorded_at；輸出choice/0.2。saved_result必為新明示來源包裝capital-saved-quantity-source/0.1，exact schema、synthetic=true、quantity_request（完整0.4 input）、generation（完整已保存0.4結果，不是actual診斷外層）。不自動找來源、不把0.4假包成after-retry／降版，不從數量或候選ID重建原來源。

純READ接線只使用標準函式庫及既有lifecycle純校驗／quantity_choice_rules；不得載入數值producer或ledger。必核request整體指紋＝generation.source_integrity_metadata.full_request_id、完整source metadata、baseline決策指紋、帳戶／截止／決策時點、研究flags全false／主壓力null、status COMPLETE且enumeration_complete。這是保存內容一致性，不是來源認證／不可偽造簽章，也不重新證明數值或全換最大量。

來源分兩種明示情況：continuation=null屬DECLARED_SYNTHETIC_OPENING，baseline不得假帶continuity；checkpoint／latest／origin ID為null而非捏造，完整原始合成account及其權利／reserve原樣保存。continuation非null屬CHECKPOINT_EPISODE，重用lifecycle._snapshot校驗完整原execution/checkpoint；核origin指紋、latest精確前身、當期account對應保存row／reserve／權利／持股、close可知時間、baseline continuity、原始資本及全部歷史／當期reviewed token。此來源讀取分支限已結清無活單、無應付且無未解除不可賣股份的既有checkpoint，不新增取消／交割能力；其他狀態明確拒絕。

source_binding綁來源包裝／generation／quantity request／baseline指紋、完整account快照、截止／decision_at、來源類別、既有checkpoint／state／execution／origin／latest、原資本、全部歷史及當期token與attempt IDs、完整quantity_domain及其指紋／asset來源身分、full_search_policy、full_search_receipt及full_proposal_status、版本。caller必明示整份相符binding。改來源／股數／reserve／latest／token／單位／通道／基底／版本／來源時點／搜尋上限或收據，不能沿舊binding借資格。

## 完整資格與端點

沿原select_candidate唯一匹配及非空文字理由；不因ID相同就認定跨generation相同資格。重用原_qualified之外，0.4必保留unit_gate_reasons及batch_gate_reasons空、候選全部targets／core targets／account一致，數量變動按明示單位核對；其他資產target不得改，HOLD沿原實股。不是重做成本／風險或新選量。

full_search政策的明示來源／時點、探測點數／合法增量序列／結果與選中FULL端點互相一致，保持完整收據，不重跑探測的財務計算。FULL僅FOUND／FOUND_ZERO_ADDITION且有唯一原成員及一致selected_target；非FOUND的plan=null拒絕。較高NOT_IMPLEMENTED不冒可選最大量。完整generation的普通grid／HOLD仍可依自身資格明示選擇，不能因另一個FULL未支援就全部封鎖。

CURRENTLY_FEASIBLE記RECORDED_RESEARCH_INTENT；WAIT_SETTLEMENT_REASSESSMENT只記RECORDED_CONDITIONAL_RESEARCH_INTENT，不升立即可買。UNKNOWN／失效／不合單位／來源錯配／完整閘門不合格／generation超限拒絕，不能轉選HOLD。FOUND_ZERO_ADDITION只表示退出A／未新增B，舊觸發不因該標籤變新買資格。不認定量最多就是最佳。

沿原Journal SELECT保存與READ讀回；成功與REFUSED都可保存。相同內容重送不重寫，ID異內容衝突保留原件，IO不明UNKNOWN。READ只校驗，不重新選、讀其他來源或載入數值producer；原來源核對check_saved沿同一新版binding分支，完整候選快照唯一成員比較，核對狀態與候選資格分開。原CLI可沿原SELECT／READ使用，不另造store／協調器／並列UI。

## 事前案例與驗收

使用unit_full_search_20261029保存input／actual：manual-93全換B93條件意圖，non-monotone全換B2一般意圖，HOLD及GRID由明示股數唯一匹配。additional-independent／first-old-fact-reviewed保存checkpoint與所有token，additional-old-trigger的FULL僅0新增，舊觸發買B格點拒絕。outer-unknown／full-A-unit-mismatch／search-limit均按原資格拒絕，不修改oracle或用新版source重跑舊結果。

另凍結來源錯配、缺／改單位或搜尋收據、錯帳／reserve／latest／token／截止、改選中股數、不合法全換、缺理由／不存在數量／重複ID、非法時間與降版輸入等反例；結構變體是READ拒絕診斷，不冒重新數值實驗。caller binding一致性與內部結構一致性分開驗。新開帳不得偽造checkpoint；既有checkpoint不得刪除後假稱新本金。

必要定向測試：保存actual符合預期，Journal相同／異內容／READ不重算、來源核對／錯配、原帳權利／reserve／latest／token不變、標準庫fresh process禁止數值producer與網路、完整Decimal環境不污染與input不變、舊0.1保存原件相容。不跑舊suite／九路徑／producer或市場回放。先凍結input／expected／版本，再實作；actual及失敗log另存，不覆寫歷史。

限合成研究意圖，正式false／主壓力null、70／2／其中8／真實合格0、1101 UNKNOWN及來源parents／圖形人工保持；R2/F、來源認證、自動解除衝突及原未支援帳務不擴張。新choice/0.2不自動接既有research_operation／supplement／比較或成交；只完成本次明示選擇及既有保存／來源核對接線。正常commit/push及固定SHA讀回沿里程碑授權；無需例行轉Work或使用者搬檔。
