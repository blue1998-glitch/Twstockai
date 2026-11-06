# 單位感知全換有界搜尋 0.4｜實作前契約

基線 d8306380f55898b153d06a853ee9e69080272fce，原工作區／分支／唯一Codex。新增 quantity_candidates-input/0.4 及結果0.4；0.1／0.2／0.3原行為與所有舊原件保持。本輪只產生互斥合成研究候選，不自動推薦、選勝者、建單、成交或擴張策略。

## 明示輸入與有限範圍

沿0.3全部欄位，新增必填 full_search：schema=capital-full-unit-search/0.1、version、parameter_source、available_at、max_probes。版本／來源非空，時點不晚於decision_at，max_probes明示正整數字串；實作資源硬上限20000次合法數量探測。這是運算限制，不是交易規則／資金預算。quantity_domain仍需完整來源／帳戶／單位；不猜1000、N或比例。

重用allocation原完整可賣／保守現金／無外部活單前置條件與原NAV／當期B價格的寬鬆界；不把權利變可用現金。A退出量必須正好符合A單位；不合就拒絕全換，不將A取整或抹零頭。B候選為原實股B加 k×B單位，k自寬鬆界內最大整數向下逐一至0。限制的是新增量，不是目標總股數。其他股、權利、一般reserve、原帳、latest／全部token均由原完整閘門核對。

先計算完整合法數量域的點數，再套明示max_probes及20000硬上限；超限整次REFUSED_SEARCH_LIMIT，候選空、enumeration_complete=false，不能暗中只試前幾個或冒完整最大量。需要原baseline求界，因此超限可以有baseline核對，但全換probe_count必為0。

每個全換點與普通候選共用同一完整build／core／resume／批次／單位閘門。首次B須當期新資金資格，追加須獨立適用觸發、原前身與全部token；不以B-family財務可行端點代替C-family追加防線。有效舊事實可重評，不算新事件。未知／失效／共用依賴／舊觸發仍阻擋新增買進。

不假設可行性單調。自上而下逐一探測，遇第一個完整閘門可行量，僅稱「本明示數量域內機械最大合法全換端點」，不是最佳比例／報酬。等待賣出交割仍為WAIT_SETTLEMENT_REASSESSMENT，不冒即時可買；沒有假定賣出已成。若較高點NOT_IMPLEMENTED，停止並標最大量未知，不能跳過未支援點宣稱較低點最大。

0新增仍須完整核對退出A；若可行，明標FOUND_ZERO_ADDITION，與退出留現金候選合併，不宣稱B新進場已獲准。所有點均拒絕時NO_FEASIBLE_TARGET，FULL的plan=null，不補假端點。HOLD／明示grid／EXIT仍沿原機制個別保留，無法全賣不會使普通減碼被抹除。

結果另存full_search_policy、full_search_receipt：原B、上界、單位、完整合法點數、明示／硬上限、逐點targets／classification／feasible／reasons／core_decision_id及probe_count。只保留必要探測收據，不新增帳本。selected_id／ranking仍null，所有正式資格false、主壓力null。enumeration_complete指明示grid已完整；full_proposal_status／receipt另表全換是否求得／拒絕／未支援。

## 事前可人工核對的正反例

主例沿原A100×10、B0×20、C2×25、現金1000／reserve100、現金權利80、A股份權利10，NAV2230。A單位2、B單位3。A100賣出滑價後999、費1、稅3，淨995；可用已結900，等待賣出交割後共同上限1895。B93成本1861.86＋費2＝1863.86，可行但等待交割；B96需1923.92，不足。寬鬆界111，探測111、108、105、102、99、96、93，不是把舊94向下取整。

非單調例在同一原帳明示情境A11／B30／C15，單股B及new群組上限45、帳戶壓力限5。原帳壓力為0；退出A後仍保留A10權利與C2，B0壓力損失10，拒絕；B1、B2壓力≤0且曝險≤45，可行；B3曝險60，拒絕。完整搜尋須找到B2，不能因0或3拒絕推定其間全拒絕。改批次UNKNOWN時原財務B1／B2仍可行，但完整外層必拒；全換不得借B-family繞過。

另凍結原B3的獨立合成opening、B單位2，目標3+偶數；不修改完整checkpoint的持股。舊觸發追加只可得到0新增或拒絕，真正獨立新觸發／有效舊事實首次審查保留。全換A單位不整除／限售／上限不足／來源錯配／未知時間明確停止。三種未來、完整Decimal環境、input不變、0.1～0.3逐bytes相容及無委託／成交控制使用既有原件。

只跑必要定向方法，不重跑舊suite、九路徑或真實producer。先凍結input／expected／source版本，actual與log另存；不改舊oracle。70／2／其中8／真實總淨合格0、1101 UNKNOWN、來源0.10全部parents及圖形人工保持。R2/F、來源認證、自動解除衝突、混合通道／容量撮合與原未支援帳務不擴張。新0.4下游選擇／回放未接；不丟失domain假稱舊入口相容。
