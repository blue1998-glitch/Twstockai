# 里程碑結果：單位感知全換有界搜尋0.4

起始原/workspace/Twstockai、dev/m1-v018-chart-annotations，本地與遠端 d8306380f55898b153d06a853ee9e69080272fce，tracked／index／untracked皆0。唯一原Codex，無代理／worktree／新分支。

## 新增能力及實際結果

quantity_candidates.generate新增明示0.4；只有這版使用新full_search來源／時點／明示資源上限。allocation抽出原前置條件與NAV／當期價格寬鬆界，舊full_transfer仍使用原整股流程。新私有搜尋由同一generator完整build函式判每個合法交易增量，沿原decide／resume、成本、現金、reserve、流動性、共同風險、資格／來源事實及批次token；未複製會計或風險公式。

先凍結22份input／expected、來源／基線與三版控制，再實作，actual另存，凍結與舊保存bytes均保持。22案狀態及所有明示斷言符合預期，包括5案ValueError、1案全次超限拒絕。這是案例數，不是獨立市場樣本或新增測試方法數。

|例子|原件結果|
|---|---|
|manual-93|完整合法點數38；依序111／108／105／102／99／96拒絕後，93可行，WAIT_SETTLEMENT_REASSESSMENT|
|unit-one|同原帳整股域得B94；舊獨立allocation.full_transfer仍得94|
|non-monotone|B0風險拒絕、1／2可行、3曝險拒絕；full得2，不作二分或單調假定|
|outer-unknown|完整探測無合格端點；FULL plan=null。UNKNOWN用C-family，除BATCH_PHASE_UNKNOWN亦保留NO_NEW_INDEPENDENT_TRIGGER，不能拿首次進場E-family正例的core feasible代稱本例core可行|
|existing-B3|合法獨立合成opening原B3，新增單位2，full達97＝3＋94；不將既有股數強制整除|
|additional-old-trigger|所有B增加均拒；只得到FOUND_ZERO_ADDITION，與退出A留現金合併，沒有新買資格|
|additional-independent／first-old-fact-reviewed|沿原完整checkpoint通過；原有效舊事實可當期重評且new_evidence_tokens=[]，不強改新事件|
|liquidity／common-risk／cost|完整閘門分別把機械全換限制至1／1／50，不當預測回報或推薦|
|A單位不整除／不可全賣|FULL分別REJECTED_DOMAIN／REJECTED_PRECONDITION，plan=null、probe0；grid／HOLD獨立保留|
|search-limit|38合法點大於明示1，整次REFUSED_SEARCH_LIMIT、候選空、probe0；求NAV需baseline核對1次，沒有聲稱core0|
|三種未來|可知research完全一致，外層完整來源指紋分開且不同|

主例可人工核算：現金1000減一般reserve100＝900；A100出售按原費稅／滑價得淨995，待到位共同1895；B93需1863.86，B96需1923.92。保存評估顯示等待賣出交割，沒有把應收或原權利即時當現金，也沒有預認賣單完成。

## 驗證與失敗診斷

本輪8個唯一unittest方法，最終8個均有PASS證據；只執行新定向方法。tests-initial.log含6 PASS、1 ERROR、1 FAIL，完整保留。diagnostics/test_search-initial.py留當時測試；ERROR是把previous_decision外層封套錯當內層並讀取不存在的token欄位，FAIL是誤認UNKNOWN會沿FIRST_ENTRY E-family，實際原機制正確走C-family且保留缺新觸發拒絕。修正測試以實際既有契約檢查，未更改任一凍結input／expected或產品原碼；只重跑兩個失敗方法，tests-corrected-two.log兩項PASS。不加成10、22或歷史PASS，也未偽造整套最終重跑log。validation-summary.json逐方法指向原log。

控制包含三版當輪修前／修後輸出完全相等；獨立原allocation端點94；相同request不變、完整Decimal精度／rounding／traps／exponent環境不污染；三種future prefix；禁止simulate及網路的主例；原checkpoint latest與全部reviewed token、原opening／account／reserve／權利保持。checkpoint路徑仍重用原ledger校驗，未聲稱整條路徑ledger呼叫0；沒有新帳或新入帳。

必要額外定向控制記於validation：高reserve950端點較93小；錯帳／錯domain明確拒；非法資源上限／未知時點在baseline前ValueError；上限20001整次拒絕；較高點NOT_IMPLEMENTED即停、最大未知，不跳過後稱較低點最大。後者是明示callback機制控制，非完整市場或ledger actual。較高未支援點的停止證據不冒原引擎已支援外部活單。

## 自審與未完成界線

allocation.py只重用／抽出原guard、bound及新增私有單位迭代；quantity_candidates.py只新增0.4分支、來源資源驗證與共用build拆分。core、quantity_domain、execution、continuity、eligibility、fact_lineage、quantity_replay及action_ledger保持原bytes。舊0.1／0.2／0.3結果完全相同；舊manifest／oracle／log／原件沒有覆寫。

完整合法域超限拒絕而不抽樣；非單調逐點向下，第一個可行值只代表此研究域最大量，selected_id與ranking仍null。其他資產／權利保持，不把指定A全退當全帳清倉。候選依原當期target風險閘門；途中未成交及執行風險沒有在本輪重播或擴張主張。

本輪不接0.4下游選擇／replay／成交，不支援混合通道、實際零股或普通盤容量撮合、信用、外部既有單完整重播、未知期初款、R2/F、來源認證／更正認證／自動解除衝突及原未支援帳務。未跑舊suite、九路徑、市場六方案、producer、資格重算、UI／Android或樣本外；不補行情或新來源。70／2／其中8／真實合格0、1101 UNKNOWN、全部正式false／主壓力null、來源parents／圖形人工保持。Astra／第一工作區救援原件仍未取得／未讀，Codex自審不冒Work原件驗收或策略有效性。

保存沿原分支正常commit／push及GitHub固定SHA讀回。讀回收據在外部暫存，避免把含自身SHA的證據循環寫入提交。無人工操作或例行Work驗收需求。下一個使用邊界是明示選擇／研究操作是否需接受0.4；目前未授權擴張，先核缺口，不能刪除domain／full_search降版。
