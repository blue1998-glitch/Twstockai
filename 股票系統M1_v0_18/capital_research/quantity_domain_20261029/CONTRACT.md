# 外部明示交易單位的候選數量域 0.3（事前凍結）

基線3dfe5b222f47f0798876687808eac98daaabe6f7，原/workspace/Twstockai／dev/m1-v018-chart-annotations、原唯一Codex。沿quantity_candidates.generate新增0.3輸入／輸出，不另建產生器、帳本或風險公式。僅合成研究候選，不接成交、策略或自動選量；舊0.1／0.2原樣保持。

## 輸入及可知時點

capital-quantity-candidates-input/0.3沿0.2全部欄位及batch_context，新增必填quantity_domain。exact欄位：schema=capital-quantity-domain/0.1、version、parameter_source、available_at、account_id、assets。version／parameter_source非空；available_at不晚於decision_at，account_id必精確屬當期完整account。

assets只含本請求incumbent與destination；每股exact code、channel_id、unit_shares、source_id、basis_id、adjustment_version、available_at。code與當期asset三項來源身分精確相符；channel_id非空外部宣告，unit_shares為明示正整數字串，不猜1000或按股號推通道。每列available_at不晚於decision_at。這是當期明示研究限制，不認證交易所實際規則、未建生效／失效歷史或混合通道引擎。來源缺失／未知／未到時點／錯帳／錯股／錯基底／版本或單位無效，明確ValueError，無假候選。

賣A及新增B各自以0為倍數起點；限制的是本候選交易變動量，非目標持股。原B3可再加2達B5；原A105按單位100可賣100留5，不能擅清零、抹權利或假借零股通道。數量上下界仍外部明示，不定本金N、比例、固定天數或策略勝者。舊請求不自動加單位或遷移。

## 完整列舉與端點

sell_A／additional_B inclusive bounds內，只列舉單位整除的合法變動量。先算兩軸合法點數及乘積，再套既有明示max_grid_combinations與1024上限；不是先跑全部整股再截斷／抽樣。不假設資金／風險可行性單調。空合法格點仍保留HOLD／EXIT／FULL等明示端點，輸出空域原因，不能判分段策略績效落敗。

所有具有targets的候選都經同一單位閘門及原core／batch／成本／資金／reserve／流動性／風險／fact history／token檢查。HOLD變動量0合法，即使原持股非單位倍數。EXIT_A_KEEP_CASH若退出量不合A單位，候選REJECTED、feasible=false，不取整或推全帳清倉。其他資產與現金／股份權利保持。

全換仍重用allocation.full_transfer及其20000限制。只有原全換端點符合兩股單位時，才接原當期重評／批次閘門；原端點不合單位時，輸出NOT_IMPLEMENTED與原端點／具體單位理由，不擅自向下取整或假稱已搜索單位約束下的最大量。0.3的enumeration_complete僅指明示有限grid完整，**不表示單位感知全換求解已完成**；另列full_proposal_status。無新求解器。

輸出capital-quantity-candidates/0.3保留原四分類及core_evaluation；新增quantity_domain與ID、兩軸合法點數、raw_integer_grid_points、空域／無合法嚴格部分A量原因、每候選unit_gate_reasons／in_explicit_grid。外層feasible_for_research必含單位與原全部閘門，不能只看core feasible。全換未支援候選plan=null；原不合單位端點留作診斷，不是可選目標。

## 事前正反例

原fixture A100／B0／C2及權利保持；A單位2、B單位2，賣0～4、增B0～4，精確9格變動組合(0,0),(0,2),(0,4),(2,0),(2,2),(2,4),(4,0),(4,2),(4,4)。原EXIT賣100合法；保存舊全換B94在單位2合法。改B單位3時原94不能冒合法full；改A單位3時原賣100不能冒合法EXIT。原A105／單位100可保留餘5；原B3／新增單位2看變動量，不因目標5而誤拒。

明示合成A1000／單位1000、賣0～1000、B增0，只有2格(0,0),(1000,0)，不是1001格，也沒有合法嚴格部分A賣量；本例不把真實N改成1000。bounds僅1～1、單位2為空grid，仍保留端點及空域理由。搜尋超限整次拒絕且core呼叫0；來源／單位錯配也在core前拒絕。

必要定向驗證含上述人工點集／各端點、unit1與舊版相容、成本／reserve／交割／流動性／共同風險、有效首次／追加新觸發／舊觸發／UNKNOWN、既有checkpoint latest／token、未來隔離、完整Decimal環境及輸入不變。只選相關原件與必要回歸，不跑舊suite、九路徑或真實producer。先凍結精確input／expected／來源指紋，再實作；actual/log另存不改oracle。

只支持單一明示單位模型，不做零股／普通盤成交、容量取整、撮合、跨通道合單、畸零權利處理或自動N／比例。所有正式資格false／主壓力null、1101 UNKNOWN、70／2／其中8／真實合格0、全部來源parents及圖形人工保持。R2/F、來源認證與原未支援帳務不擴張。沿里程碑自審、正常commit/push及GitHub固定SHA讀回；無代理／分支／worktree、bootstrap／市場回放或部署交易付費訊息。
