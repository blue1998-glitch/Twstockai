# C類已核准條件買單同單重評 0.1

基線5be3d8bea1008361642b3ec3a6bfdafaa16373a9。只補已核准C/R1原條件買單的同單重評；原family、trigger IDs、原order及remaining上限不變。新批仍要求新獨立觸發，不刪token、不改C為E、不新增數量或第二帳。

## 明示版本及入口

conditional_quantity_review新增輸入／輸出0.2，僅C原單續評。原0.1仍只B/E，行為／版本不變。原數量候選0.2與回放0.1用於最初核准，不能注入raw plans／外部checkpoint。

core.resume_decision新增same_order_id的明示續單參數；只有先通過原checkpoint／最新前身／當期帳戶檢查，且原單作用域驗證成功，才適用。普通decide、新批resume及原0.8路徑沒有此參數時，NO_NEW_INDEPENDENT_TRIGGER規則不變。輸入JSON自帶旗標／proof不能取得權限。

新C續評決策為capital-decision/0.9，附capital-same-order-scope/0.1證明；execution中實際有0.9決策／attempt才成capital-execution/0.9、checkpoint0.8。較早prefix仍0.8／0.7，未可知的未來review不能先改早期狀態。原0.8／0.7結果不重算、不升版，原old READ可續讀；新schema由必要讀取接線明示支援。

## 原單作用域

- 只限本回放中原C/R1決策核准的唯一活躍BUY單，仍requires_reassessment、remaining>0、未取消／到期，原order首次核准時間與原decision精確相符。不是任意外部舊單完整重播。
- 原提案必為feasible且trigger IDs非空、唯一、屬同股票／source／basis／adjustment。每個原觸發在原核准時確為新獨立token；目前需保留全部歷史token，不把有效舊事實變成新事件。
- 本次fresh plan只有該原方案，id／family C／R1／trigger IDs精確保持。所有其他資產target等當期實股，原單股票target只能當期實股+原remaining；超量、較小目標、其他買賣或換單都拒絕此續單用途，應另走明示取消或新批規格。
- scope綁原order指紋、原decision／candidate、原trigger身分及tokens、原單量／remaining、已成交fill IDs、checkpoint、latest前身、共同帳戶與來源基底。新review ID、別名或共柱不能繞過。
- 續單只豁免該C plan「必須是全新trigger」檢查，不豁免當期新資金資格、事實歷史、期限／撤銷／衝突、成本／資金／reserve／流動性／共同風險；失效或未知仍拒絕，原attempt與限制照原機制保留。

## 執行及帳務

原生reassessments帶明示same_order_review schema及同一order_id，原引擎重建真實prefix，再調用scope驗證，不能信任外部手填proof。接受後只續用原限價、期限、order ID及remaining；無新單、無預認出售成功或應收可用。部分成交／未成交、取消、原cash／share權利、一般與委託reserve、latest及全部token沿同一原帳。成交／交割本身不批准下一批。

必要snapshot驗證對0.9決策驗scope指紋及其原order／decision／觸發／帳戶／checkpoint身分，拒絕scope丟失或改寫；不建通用來源認證、身份合併或更正引擎。READ只投影已保存版本，不能調數值引擎重建歷史。

## 本輪證據

先保存明示合成input／expected／source版本，再實作。起點沿原A100、C2、cash100、reserve100、cash claim80及A10權利；明示已有B5，原帳capital1430；新B-event為尚未用過的獨立觸發，初始C方案新增B20並賣A50，待交割重評。這是合成假想，不是使用者實際部位或市場資格。

必要正反例含：合法同單B20／部分B7、失效／UNKNOWN／衝突、原family／trigger不變與new_evidence_tokens不造新、超量／改單／錯股／錯來源基底／錯前身或帳戶／checkpoint、未交割／成本預留或風險不足、新批重用舊trigger拒絕、真正新觸發新批正例、原E0.1必要相容與舊READ，以及未來撤銷隔離。輸入、expected與舊actual不覆寫；不累加中間批／歷史PASS，不跑整套舊suite或真實producer。

全部正式資格false、主壓力null；1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0及來源0.10全部parents保持。R2/F、信用、期初應付及外部活單完整重播等不擴張。不改正式策略／圖形／人工模式，無新來源、私人文件、bootstrap、UI／Android、樣本外、部署、交易、付費或訊息。Astra與第一工作區救援原件未取得／未讀。
