# 分批換股數量候選產生器 0.1

這是本輪唯一功能里程碑。純核心 `quantity_candidates.generate(request)` 只產生原股A、候選B、現金之間的數量意圖，不選最佳比例、批數、天數或勝者。其他資產、現金／股份權利、reserve、前身及token保持。資金框架沿用0.8，不改原會計或歷史schema。

## 輸入 capital-quantity-candidates-input/0.1

- synthetic=true；decision_input為既有capital-decision-input/0.1。incumbent／destination是明確不同的現有股票。A須有正整股持倉。輸入plans不作生成器的額外候選，不接受family／route覆寫。
- bounds.retained_A.minimum／maximum：明示保留A的整股範圍，1≤min≤max≤目前A股數。bounds.additional_B.minimum／maximum：明示新增B整股範圍，0≤min≤max。每格步長1、完整笛卡兒積，不抽樣或二分猜單調。範圍只限制部分配置域；另列續抱、A全退出留現金、既有full_transfer全換端點。
- max_grid_combinations：本次明示的計算預算，正整數字串，實作硬上限1024格。這是工程資源界線，不是正式交易門檻。格數超過任一預算即REFUSED_SEARCH_LIMIT、候選空、enumeration_complete=false；沒有部分結果冒充完整。
- trigger_ids：本股B的明示獨立事件ID；所有新增買進固定產生family C，再沿0.8去重／有效期／資金／成本／風險／流動性檢查。不能改成B或E繞過下一批觸發。有效舊事實可經當期review繼續提供資格，但不變成新的獨立觸發。共用形成點／量柱／事件仍沿既有token判定。
- policy：version、parameter_source、available_at、edge_budget。版本／來源必非空、時間須在決策前可得；edge_budget為明示合成參數，不是預測報酬。本次所有生成意圖含full_transfer使用同一edge_budget。
- continuation=null或{previous_decision,checkpoint,cancelled_order_ids}。有續接必逐候選使用resume_decision精確證原帳／權利／latest與完整token；沒有checkpoint不得宣稱連續資本鏈。不得把baseline本輪剛review的tokens再灌回同輪競爭候選，候選不是順序交易。

## 生成與檢查

1. 對同一帳戶建立0.8 baseline（plans=[]），續接時沿resume_decision。沿用baseline的A-zero，即使風險超限仍保存並標拒絕，不升為合格研究候選。
2. 明示域列舉每組保留A／新增B。新增B=0為減碼留現金；新增B>0為部分換股／由既有現金增持B。保留其他股票的實股目標，所有原帳權利不動。另列A全退出留現金。
3. 全換只呼叫原allocation.full_transfer，不重做完整配置算法；其內部既有有限降序界線20000沿用。產生的目標還須在當前continuation／歷史下重新檢查；新增B一律改接family C及相同觸發。原builder是snapshot提案，不把其結果當跨輪已認證最大量。既有full builder超限時整次REFUSED_SEARCH_LIMIT，不輸出已列前綴；有外部既有單等不支援時全換單獨NOT_IMPLEMENTED，其他可檢查意圖仍保留。
4. 完全相同目標合併kinds，不重複計持股或資本。每個不同目標獨立由decide／resume_decision檢查；沒有第二份帳、執行器或資金預算算法。所有buy>0都固定family C；API拒絕未知頂層／bounds／policy欄，沒有family逃生入口。原任意plan API沒有被改造成通用來源／策略認證引擎。
5. classification分CURRENTLY_FEASIBLE、WAIT_SETTLEMENT_REASSESSMENT、REJECTED、NOT_IMPLEMENTED。既有CONDITIONAL僅映射為等待交割後重評，絕非已可買進。成本、實股／待交權利及既有委託共同風險仍由0.8處理；當期目標可行也不保證途中退出／成交。

## 輸出 capital-quantity-candidates/0.1

research含同一0.8 baseline、各候選plan與原可行性結果、共同account ID／初始資本、kinds、分類、完整列舉範圍與上限。無ranking／winner／order／fill。各分類只是待研究清單，所有正式資格false、主壓力null；不把靜態scenario_values/Pareto變成政策績效。

source_integrity_metadata在research之外，綁完整輸入指紋及原來源metadata；未來來源尾段可不同。相同當時可知前綴的research須一致。已有actual時只讀，不重算覆寫。新功能與任務規則整合入既有AGENTS／CONTINUE及capital_research README，不另立平行工作政策。

## 預先凍結的有限驗收

合法部分換股、減碼／全換重用、有效舊事實重評與新獨立觸發、同事件／共用量柱重複觸發、失效／未知、資金／reserve不足、等待交割、非單調可行集合、列舉／full-builder超限、未來資訊隔離；另驗原帳／其他資產／權利／reserve／latest／全部token及不變性。

1101 2026-01-02期初cash_claims仍為帳戶證明阻塞、UNKNOWN與拒算，不找公開資料補、不收私人原件。來源0.10及parents、正式action_resolution0.4、70／2／其中8／真實總淨合格0保持。信用、R2/F、來源認證及原未支援帳務不擴張。真實producer、市場競爭、舊整套suite、九路徑、UI／Android與樣本外均不執行。
