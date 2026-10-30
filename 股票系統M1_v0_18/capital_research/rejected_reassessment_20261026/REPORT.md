# 遭拒中途重評：限制收件保全 0.7（本地未提交）

本輪基線為遠端／本地 `135f73b65e9622a664fcf05adb4cdb09a9c70e02`，起始 tracked/index/untracked 均0。使用者只授權定向重現、最小修復及必要測試，**沒有 commit/push 授權**。只用原唯一 Codex／原工作區；以下全部為明示合成研究，不是市場績效或正式交易資格。

## 實際結論

疑點已實際重現。0.6 中途重評遭拒後，fresh decision 與新限制未進入 execution/checkpoint；恢復舊原件後，B 資格與 E-partial 重新放行。原已備款舊單也能在同一次觀察買入 B20。修前／修後均沿原 action_ledger、原始資本2180、reserve100、現金權利80及股份權利A10，沒有第二帳。

|案例|0.6 保存 actual|0.7 保存 actual|
|---|---|---|
|restrictive-unfilled|恢復原件 B qualified=true；候選包含 E-partial；舊單 OPEN|B qualified=false；候選僅 A-zero/D-cash；FACT_RESTRICTION_CONFLICT_UNKNOWN；舊單取消|
|restrictive-funded-fill|遭拒後仍沿原決策買 B20|同觀察、成交前取消，B 成交0|
|value-only-rejection|拒絕 value 改寫；有效舊單 B20 成交|仍 B20 成交；拒絕提案不取代 latest|
|valid-review|當期合法重評後 B20 成交|仍 B20 成交；latest 指向合法重評|
|conditional-rejection|原單 requires_reassessment=true，未成交|仍未成交；新增限制另留下取消紀錄|
|future-prefix|本輪未對0.6重現此補充案|截至1/9，未來撤銷不進入數值歷史；舊單 OPEN、未成交|
|future-known|本輪未對0.6重現此補充案|1/12 09:01 可知時取消；B成交0|
|future-partial|本輪未對0.6重現此補充案|保留1/9合法 B7；1/12取消剩餘13；費用／應付交割一次入原帳|

主例原件：`before-final/<case>/` 與 `after-final/<case>/`。每案先保存 specification、first-input、expected、source-versions；checkpoint、review-input、完整 input 均在相應 numeric call 前保存，再另存 actual。`restore-actual.json` **只證恢復原件後資格與候選，不證第三輪成交**。沒有新增1/13行情。

## 最小輸入與時序

重用已保存0.6 `mixed-null-revocation/first-input.json` 的原帳、權利、來源、基底、成本、明示日曆與1/12視窗。選 E-partial，只送 B20 BUY（原契約容許目標差量的子集，不必假定A已賣）。限價20.03，已結現金1000、一般保留100；1/6容量0，1/8 16:00 checkpoint。

fresh decision 為1/8 17:00、資料截止1/8 16:00；同scope B-event改寫value，將原有限期限1/20縮至1/10 16:00，無來源更正。重評當下期限尚未到期，但新舊內容衝突使方案不合格。1/9 A09:00只更新估值、沒有A成交；B09:01處理重評，checkpoint_id／decision_id都由原流程精確產生。故沒有觸發「cutoff後隱藏成交」或活單跨交易日取消的既有拒絕。容量0／100分成資格保全與備款成交兩案。

資格保全案觀察至1/9日終，1/9 17:00精確承接原latest與帳戶，恢復 B-event 原bytes；沒有等待應付交割問題，因該案無成交。備款成交案獨立保存 actual，不冒稱有立即續接未交割買入。

## 修復與版本

`execution.py` 在精確checkpoint與decision_id核驗後，不論方案接受／拒絕，都保存 `reassessment_attempts`。拒絕者不進 accepted decision_ids、不替換 latest、不執行其提議的取消清單。其原始 fact_source、決策、原因、收件時間、token及指紋完整留存；相同attempt不重複處理。**保留限制宣告不是認證該宣告為正確來源。**

`reassessment_history.py` 提供純資料接線，拒絕收件以 receipt 包裝加入既有 fact_lineage；生效不早於實際 observed_at 及宣告時間。execution 在同觀察成交前再次核對原單依據的限制。純value／期限放寬提案遭拒、卻沒有新增限制時，不把提案的改寫理由當成原單失效；原root的有效期、撤銷、UNKNOWN與限制衝突仍完整檢查。

`continuity.py` 核驗attempt指紋、前身、原始來源重建的候選歷史、方案結果、收件時間與事件引用，checkpoint包含原execution receipts，state fact_history由所有已收件宣告重建。`core.resume_decision`沿同一來源接線；所有已review token（含拒絕提案看到的新事實）帶到下一輪，不把它們變成新獨立事件。原 action_ledger、原帳 opening、fills、權利、未成交狀態、一般reserve保持。

新 decision/execution/comparison=0.7；checkpoint=0.6；fact-history=0.3；新增 attempt/receipt=0.1。舊JSON READ原樣，不重算、不隱式遷移；舊checkpoint拒絕作新續接證明。

## 驗證與保存

最終 `tests-final.log`：**24唯一方法PASS＝15新＋9直接必要回歸**。修前單例FAIL為這24方法之一；6／14中間批不累加。歷史25／35／20／38／51／46都不計本輪。`verify.py`列出精確方法，檢查方法ID不重複；沒有跑整套舊suite或真實producer。

修前首批 `before/` 的主例已重現；最後 conditional 對照原用B99，在reserve100下不能支付成本，先被既有可行性擋住。該診斷／log原樣保留，沒有把它當成主疑點反證。`before-final/` 只把該對照目標改B90，仍無A賣單，因此可測「可行但必須等待交割／重評」防線。主兩案與其他正例輸入／oracle沒有跟著改；五案 expected與first-input在before-final／after-final逐bytes相同。

`baseline_0_6/files`封存25份原source／根交接／原帳模組，inventory固定長度／SHA；0.6固定提交可回查全部原件。`artifact-audit.json`實核26個最終source指紋、25份封存、五案輸入及oracle同bytes、原帳模組未改。`source-diff-from-0_6.patch`含四個現有模組及新增純接線模組；新測例／fixture另在本目錄。所有舊 evidence_conflicts／evidence_lineage／repair／validation及其oracle／log不改。

部分成交補充案的保存execution actual逐日沿原帳：1/9買入7、保留13，未來限制可知後才取消13，1/12交割後settled_cash=938.860、shares=A110/B7/C0、purchase_payable=0、reserve100。定向方法核此checkpoint；既有兩項部分成交跨輪必要回歸也本輪實跑。**沒有另存新的0.7完整跨輪部分成交execution actual，不能以終點相等宣稱任意中途資金未重用。** 獨立新事實／新token等有本輪方法與log，並非每項都有完整逐輪JSON。

## 邊界

本修復只處理已通過前身／checkpoint／decision_id核驗、實際送達executer的重評。錯checkpoint、錯來源或未送達的review，不會因此取得自動可信收件資格；沒有通用外部事實認證／非同步消息攝取。收件時間不是回溯撤銷已合法成交的授權。舊單正例只保護明確相同scope／accepted body；不是任意舊單永久有效。

完整更正／分叉矩陣、合法來源更正、自動解除衝突、複雜身份合併、較晚valid_from獨立案例、R2/F及原未支援帳務仍未完成。真實producer、資格重算、市場六方案、UI／Android、樣本外未執行。正式action_resolution0.4、來源0.10及全部parents、P0-3/P0-4、reaction_facts／人工基底不改；70拒算／2不足／其中8換股未支援／真實總淨合格0、全部正式false、主壓力null保持。

Work可讀GitHub保存0.6，不等於取得本地0.7或獨立驗收。Astra、第一工作區救援原件仍未取得／未讀；未等待、重建或推定890檔存亡。本輪未commit/push／部署／交易／付費／訊息，無子代理、worktree、bootstrap/hydrate。
