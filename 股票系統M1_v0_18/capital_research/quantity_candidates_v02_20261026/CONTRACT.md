# 數量候選0.2：沿既有0.1補齊需求

本輪沿原quantity_candidates.generate實作，不建立第二產生器、帳務、風險或成本公式。core／execution仍0.8，allocation.full_transfer原限制不改。0.1已保存成果原樣READ；0.1輸入路徑維持原行為，0.2才使用下列新契約。舊九路徑／oracle／actual／log／manifest均不重算覆寫。

## 輸入 capital-quantity-candidates-input/0.2

沿0.1所有欄位，新增必填batch_context；bounds改成sell_A與additional_B，兩者都是minimum／maximum整股字串。sell_A可含0及全部A實股，0≤min≤max≤A實股。賣出超過可賣／被委託鎖住時仍完整列舉並委派0.8拒絕，不靜默截斷至可賣量。新增B是本候選新增量，不包含已存在待買委託。完全相同目標合併生成角色。

policy.version／parameter_source／available_at共同綁定bounds、max_grid_combinations與edge_budget；model／cost／risk／buffer的原來源與可知時間繼續由0.8檢查。無可得來源或未到時點拒絕，不推價差／壓力為預測報酬。部分域完整單步枚舉，上限沿原1024格；全換沿原20000界線，超限整次候選空，不抽樣。明示域可包含賣完A但僅買少量B，與full_transfer機械端點不同；其他資產與A待交權利不因此消失。

batch_context欄位固定：version、parameter_source、available_at、phase、origin、code、source_id、basis_id、adjustment_version、account_id。account_id是原完整account指紋；code及來源／基底／版本須精確屬B。這是明示合成研究階段，不是投資人歷史／來源認證。

- phase=FIRST_ENTRY：新資金資格仍由0.8檢查，但不強加新獨立事件條件，生成family E數量意圖。沒有continuation時origin必為DECLARED_SYNTHETIC_OPENING，明示本次假想帳戶起點；B實股、B待交權利、B待買單須無既有參與，也不能有已消耗B事實token卻缺歷史的未知情況。有continuation時origin必為CHECKPOINT_EPISODE，由原驗證過的opening、全部fills與既有B買單歷史核對；即使B目前零股，曾持有／有買進或已批准B單也不得改稱首次。有效舊事實在未買過B的合法checkpoint可經當期review支持首次買進，不變新獨立事件。
- phase=ADDITIONAL_BATCH：新增B固定family C，沿全部舊token、當期B已知前綴、有效性及相依token核獨立新觸發。不能用family、ID、別名、新review或FIRST_ENTRY標籤重置已知批次歷史。
- phase=UNKNOWN：保留續抱／減碼，但所有新增B拒絕，不能默認首次。
- 有既有B待買委託：原單保持，不生成撤單／重下／成交。原0.8預留與共同風險仍計入；新B批次因未支援完整外部活單承接明示NOT_IMPLEMENTED。不能把原單當零或將其數量重算成新批次。

## 輸出 capital-quantity-candidates/0.2

沿原四分類、原0.8core_evaluation及獨立batch gate。外層classification／feasible_for_research是完整研究閘門；不能只看core_evaluation。新增sold_A、生成理由、階段核對理由與policy涵蓋範圍。EXIT_A_KEEP_CASH僅退出A實股，不是全帳清倉；C等資產、現金／股份權利保留。

候選無最佳數量、排名、委託、成交或資格提升。來源完整性metadata在research外，未來尾段可不同；同當時可知前綴research須相同。語義不相容輸入以明確ValueError拒絕，合法但缺階段證據則拒絕新增買進。真實資料不得改標synthetic繞過資格。

## 本輪有限驗收

獨立人工9格清單、含全賣A的有限域、首次有效舊事實／追加新事實、偽首次與UNKNOWN、來源／基底錯配、成本／reserve／應收／流動性／共同風險／鎖股、待交割、既有B活單預留、不單調／兩種超限、三種未來尾段、輸入不變及原帳／latest／權利／token。只跑本輪定向集合及少數0.1相容回歸，不重跑原0.1整套、舊九路徑或真實producer。

本輪允許一般工程、自審、正常commit/push與GitHub讀回；依原AGENTS／CONTINUE有效功能里程碑規則，不另建平行工作規則。1101 2026-01-02期初cash_claims仍UNKNOWN／拒算，不補公開來源或私人文件。70／2／其中8／真實總淨合格0、全部正式false、主壓力null、來源0.10與parents／正式action_resolution0.4保持；R2/F、來源認證、自動解除衝突、原未支援帳務、真實績效、UI／Android及樣本外不擴張。
