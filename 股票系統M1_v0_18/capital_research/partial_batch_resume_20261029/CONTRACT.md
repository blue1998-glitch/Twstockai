# 新批部分成交後重用原續播 0.1（事前凍結）

基線5c6d04b487375f85f611ef34cc2fdbdc0037e583，唯一Codex原工作區／分支。只補「原帳結清 → 明示新批 → 新批部分成交 → 續原單交割／到期」的有限合成接續驗證。重用cash_action_execution.execute、execution_continuation.resume_orders及原ledger；不新增產品入口、策略、委託、批次或帳務公式。只有actual證實缺口才修復。

## 原件與精確模型

`settled_resume_action_20261029/actual/independent-B20/result.json` 已保存完整原job及前身：1/8 16:00原帳B7/C2、已結858.86、一般reserve100、80現金權利與C2股份權利；舊explicit-order剩13已到期。新獨立B-step2及second-B-buy20的當期資格、原觸發／來源、限價20.03、期限1/12 12:00、日曆／close proof／窗口均保持。這些是已明示合成研究參數，不是使用者交易數量或政策。

本輪建立**另存模型**：將該job的tape全文換成 `cash_execution_20261028/cases/partial-7-active-13/input.json` 已保存的1/9 A/C/B tape；只有B容量從500變成既有7，價格／available_at／市場狀態／來源／基底／交割日全部相同。不得把舊B20全成actual改成B7。完整root_job先凍結到1/12 16:00，prefix只觀察到1/9 16:00；沿原execute生成prefix execution與完整checkpoint。

## 獨立手算預期

| 水位 | 已結現金 | 應付 | 嚴格可用現金 | B實股 | C實股 | 新單剩餘／預留 |
|---|---:|---:|---:|---:|---:|---|
| 原1/8 | 858.86 | 0 | 858.86 | 7 | 2 | 尚未成交的新單20 |
| 新批1/9部分成交後 | 858.86 | 141.14 | 717.72 | 14 | 2 | 13／261.65039 |
| 1/10日終保存（原明示非交易日close） | 858.86 | 141.14 | 717.72 | 14 | 2 | 13／261.65039 |
| 1/12交割／到期後 | 797.72 | 0 | 797.72 | 14 | 4 | 13到期／0 |

新成交7×20.02＋原費1＝141.14；不在1/9先扣成已結再於1/12扣第二次。797.72＝858.86＋原80權利－141.14。一般reserve100另外保存，80應收與C2股份權利未到期前不當現金／實股。原本金1180保留，沒有另注資或重開本金。原7與新7各保留原fill ID，新批剩13與舊到期13分屬兩張原單，不能混用或復活。

1/9之後沒有其他明示執行觀察。本輪path必逐原交易日宣告完整合成機會，含1/12空日no_other_execution_opportunities=true；這是明示模型假設，不是市場「沒有成交」證明。續播只處理已接受fills的交割及原單到期，不宣稱剩13再成交。不新增行情、移動原tape時刻或延長1/12窗口。1/10只用已保存的原calendar與close proof，不推新交易時段。

## 事前驗收

先存契約、full root、prefix外部請求、來源指紋、手算預期及反例規格，再執行新prefix；原已保存前輪及其producer只READ。prefix產生後先保存完整resume input與expected，才呼叫原resume_orders。

1. 1/9→1/12一次續播，及1/9→1/10→1/12兩次續播，均須等於同一完整root的一次執行。比所有共同明示觀察、每日ledger、完整終態execution/checkpoint，不只終點淨值。完整source/path指紋與數值狀態分開。
2. 原job.continuation中的完整原帳／前身，舊fill、已到期單、新部分單、reserve、fact／重評歷史、精確latest及全部12個token均保存；續播不新增決策／token／委託／fill。內層new_fill_ids仍屬當前root job累計；外層new_fill_ids_this_segment須空。
3. 五個拒絕反例：把expected_latest換成前一輪ID；刪root_job.continuation；改用同一新批但容量500的完整路徑配B7 checkpoint；重複checkpoint fill；漏1/12空日完整性宣告。分別預期EXACT_LATEST_PREDECESSOR_REQUIRED、Opening ledger/cutoff mismatch、PREFIX_EXECUTION_MISMATCH、Execution fingerprint conflict、COMPLETE_SESSION_COVERAGE_REQUIRED；拒絕不得啟動尾段。
4. 所有input不變，原件／source／oracle指紋保持。既有入口未變時重用數值環境／未來隔離證據，不重跑舊suite、完整producer或市場矩陣；只計本輪實際唯一測試方法。

root決策期初仍是已結清1/8帳，不能把部分後的應付塞回假新opening；1/9的payable由完整原fills與checkpoint承接。保留所有舊拒絕、UNKNOWN、70/2/其中8/真實合格0、正式false／primary_pressure_id=null及來源parents／圖形人工。不擴外部單、未知期初款、限售、來源認證、R2/F或完整分叉。不部署、交易、付費、對外訊息，不開代理／worktree／分支；沿里程碑自審、正常commit/push及GitHub固定SHA讀回。
