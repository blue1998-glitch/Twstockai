# 獨立公司行動資金帳 0.1

純數值 `action_ledger.py` 不讀檔、不連網、不下單；外部 `action_sources.py` 讀已存原件，`action_study.py` 明確產生新資料。舊 `rotation-input/0.1`、core／loop／store／CLI、P1-7價格報酬與舊圖不變。新輸入 `rotation-action-input/0.1`；輸出 `rotation-action-ledger/0.1`，比較 `rotation-action-comparison/0.1`。

## 資料綁定

- RAW專用，Adjusted拒絕，避免股利／配股重複入帳。`assets` 的 source_id／basis_id／quote_source_ids、事件同 code／basis_id、來源URL／SHA256／captured_at都須保留。精確數字為十進位字串，50位Decimal算術，JSON不降為float。
- 每事件id是除id外全部內容的canonical JSON SHA256。必要欄位必須有source_id及locator；指紋只驗一致性，不能認證事件真實或一段期間沒有其他事件。來源模組才核對原件雜湊、讀取定位與已保存輸入。
- `ex_date` 是本帳經濟生效日：現金／配股用除權息交易日；減資用已核股數轉換生效日。減資停止／恢復交易日不能自行當同一天。`announced_at`、record_date、delivery_date、pay_date、tradable_date各自獨立，不以股東會日、擷取日或發放日代替公告／可交易日。
- 完整calendar須逐曆日給明確trading旗標。coverage須對每股涵蓋窗口、現金／配股／減資、其他行動檢查、來源及精確事件清單；缺事件不等於零事件。尚不支持合併、分割、現增認購等會計，出現則拒算；不能在coverage宣稱已檢查但將它們省略。
- qualification是外部經核對後的**宣告**，純核心不會替呼叫者取得或認證原件。缺淨分配、期初權利、完整行動／日曆時直接REFUSED，無每日帳、無任何總淨報酬。

## 逐日順序及守恆

起點為明確起日**收盤**，期初持股、可用現金、既有現金／股份應收分開列；ex_date等於起日的事件不再重記，須從期初應收證據接續。當前持股不能倒推出已賣出的除權持股權利。

1. 按前一日收盤持股登記生效日權利，再處理已明列的成交。除息日賣出仍保有權利；當日買進不補領。僅算已知發生事實，不生成交易訊號。
2. 現金股利須有gross_per_share、**有來源的net_per_share**及pay_date。應收增加淨資產但不是可買進現金；發放於日終由應收轉現金，不再增加一次收益。沒有實際入帳資料的公司預定時程不是實際到款。
3. 配股須有shares_per_share、delivery_date、tradable_date，金額不是股份比。股份應收、交付紀錄、可交易持股分開；原股賣出不取消已取得的配股權利。未可交易前不可賣；零股權利保留並拒算報酬，不猜面額／零股變現率或默默截去。
4. 減資從舊股扣除、轉為新股應收，同時建立有來源的淨退還資本應收，另記現金支付及新股可交易日；不記成股利收入。清掉舊價標記，缺轉換後真價就留null並拒算，不能用舊價補出NAV。待入帳權利又遇新行動的重疊權利口徑未支持，明確拒絕。
5. fills只接受顯式日期、前一日或更早decision_date、side、股數、有效價、fee、tax、settlement_date及source_ids。買進預留應付、賣出建立交割應收；應付從淨資產扣除，不把未結算價款當免費持股。只用已結現金，未實作券商額度／同日淨額信用。沒有自動策略或下單；不重用舊無股利成交來假裝已重新模擬有股利策略。
6. 每曆日保存已結／可用現金、現金應收明細、買進應付、持股、待交股份、原價來源日期／基底與權責淨資產。非交易日只可沿用明列來源日期的估值標記，並非捏造K線；交易日持股缺價留null並拒算。不外推行情。

## 報酬及比較資格

`scenario_net_return`：明列參數的帳務情境，終點權責淨資產扣已給定費率／最低費／賣稅／滑價的估計退出成本，再除期初權責資產減一；期初不是歷史買入成本。不年化、不選最佳比例。待分配零股、未可交易股份、持股缺價等情況無報酬。

`total_net_return`：除上述完整資格外，來源均為官方原件／券商紀錄，且execution_costs為VERIFIED_EXPLICIT_MODEL或VERIFIED_ACTUAL才可輸出。前者仍是**來源合格、按明示成本的總淨報酬研究**，包含股利及股數轉換，不是投資人實現績效；估計退出費不冒充實際賣出。未驗歷史公開可得不能升當時可交易訊號，historical_signal_eligible始終false。

`actual_realized_investor_return`：更嚴格要求實際成本與現金流已核、終點全現金、無應收應付；否則null。不能用宣告旗標取代原件人工驗證。

compare只比較同起訖、同初始權責資本的顯式帳戶；全部來源合格才給期末淨值兩兩差額。任何不合格則無差額與無排名，不選主壓力或勝出策略。primary_pressure_id=null；policy_authorized=false。

## 保存及使用

`python3 -m rotation_research.action_cli RUN --input rotation_research/action_data_20261022/engineered-input.json --store /tmp/m1-actions-demo --id cash-demo`

`python3 -m rotation_research.action_cli READ --store /tmp/m1-actions-demo --id cash-demo`

重用未修改Journal，exclusive write、fsync、同id內容衝突拒絕；READ不import數值核心、不修復或重算。保留其單檔／父目錄fsync／多程序及斷電限制。engineered輸入是帳務測試，不能作行情或市場投資績效。實際來源probe會存下REFUSED結果。
