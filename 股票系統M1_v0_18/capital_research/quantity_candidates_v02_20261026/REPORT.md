# 同一數量候選里程碑：0.2有限補齊交付

起始實核遠端／本地HEAD為c1e59f1f1a39d8b2b56b217eb07f25c53d8b1726，使用者已知1b200d681a6b68168c45591775e107174f064138為祖先。原分支／工作區、tracked修改0／index0／untracked0。重用已交付0.1，沒有平行重建；本輪明確授權工程、自審、正常commit/push及GitHub讀回。

## 真正補齊的能力

1. 0.2以明示A賣出量與B新增量完整枚舉，sell_A可含0與全部A。原0.1只能保留至少一股A的部分域，除單一全換端點外無法列出「A全賣、B僅配少量」；本輪已補。其他資產與完整原帳權利保持，退出A不聲稱全帳清倉。
2. 首次與追加分開。FIRST_ENTRY須當期新資金資格及同帳／同B／已可知的階段宣告；原checkpoint證未有B參與時，有效舊事實即使已review也可支持首次，不強制變新事件。ADDITIONAL_BATCH仍family C、全部token與新獨立事件；改首次標籤不能抹掉原B交易／委託／持有或失效歷史。UNKNOWN阻擋新增B。
3. 既有B買單保持原樣。0.8仍扣其預留與共同風險，本生成器不撤單／重下；新批次完整外部活單承接未實作時明示NOT_IMPLEMENTED。不重複把原單數量當新批次。

核心／execution仍0.8，原allocation.full_transfer、資格、成本、資金、風險與fact_history機制不改。新功能只加研究輸入／域／階段接線，沒有第二會計、風險公式、最適化、委託或成交。

## 保存actual與有限驗收

先保存CONTRACT、baseline-sources、27份input／expected及intake，再修改source並存source-versions-before-run，才執行新版本。全部cases/*/actual.json是本輪最終source結果，與原輸入／oracle及source版本綁定；本輪無中間失敗或oracle修改。

|驗收|保存案例及實際結果|
|---|---|
|人工小域清單|first-manual-grid的獨立9格清單：A100／99／98 × B0／1／2，完整保留，再加獨立退A及原full_transfer端點；沒有抽比例|
|全賣A而部分配B|all-A-sale-partial-B含A1／0 × B0／1／2共6格，A0/B1可行；C實股2及A待交權利仍在原帳，非全帳清倉|
|首次有效舊事實|first-old-fact-reviewed：合法未買B的checkpoint、舊B-event已review仍可提供資金資格；A100/B1當期可行，觸發清單空，非強迫新事件|
|追加新獨立觸發|additional-old-trigger拒絕，additional-independent可行；原形成點／事件／量柱與全部token機制沿0.8，0.1兩個相容例仍完全相同|
|FIRST不能洗掉歷史|cannot-relabel-first-after-fill保留原部分fill／最新前身，FIRST仍拒絕；cannot-reset-first-without-history有已消耗B token卻無鏈證明也拒絕；unknown-batch-phase拒絕新增|
|資格／失效歷史|first-capital-unknown、first-invalidated及known-history-not-erased拒絕新資金；新review不自動恢復已知撤銷|
|來源與基底|review-mismatch-source_id及review-mismatch-basis_id是明確ValueError／research=null，不偽裝成功零成交或零候選|
|成本／預留／應收|cost-cannot-be-free只剩21已結可用，B1含成本超出而拒絕；receivable-not-spendable有80應收但可用仍0，不能買B|
|流動性／共同風險／鎖股|liquidity-limit、common-risk-limit與sell-locked-A分別沿0.8列ENTRY_LIQUIDITY_LIMIT、RISK_LIMIT_EXCEEDED、SELLABLE_SHARES_RESERVED_OR_UNAVAILABLE，不用新公式|
|交割等待|wait-sale-settlement的A95/B1為WAIT_SETTLEMENT_REASSESSMENT，沒有立即可買或成交聲稱|
|既有單不動|existing-B-order原買單完整保留；900減其22預留後可用878，只扣一次；新B意圖與全換端點為NOT_IMPLEMENTED，沒有撤單／重發|
|不單調／超限|non-monotone保留B0拒／B1、2可行／B3拒的集合；grid-over-limit及full-over-limit整次候選空、enumeration_complete=false|
|未來隔離|future-A-wins／future-B-wins／future-both-fall的整個research與first-manual-grid相同，只有外層原件完整性metadata不同|

本輪27個定向案例全部符合凍結預期，包含兩個預期輸入錯配拒絕。14個必要測試方法一次PASS，重用上述保存actual；其中一方法只跑兩個0.1相容案例（legal-grid、shared-volume-trigger）確認舊API結果相同。沒有重跑0.1整套18方法、21案例、九路徑、舊prefix producer或其他舊suite；不把原PASS／案例或兩個回歸再相加。

方法內另檢查輸入不變、階段帳戶／基底錯配、未到可知時間及空參數來源；其證據為原碼與tests-final.log，沒有冒稱每個變體皆有完整保存JSON。自審另外逐項核完整目標集合、同原資本／權利／reserve／latest／全部token、舊檔指紋與root歷史正文。

## 集中額外複核及限制

本輪原唯一Codex完成自審，不預設另轉Work。重大接線複核項：FIRST的同帳邊界與B參與歷史不可重置；有已review舊事實而無B交易的checkpoint不永久封鎖；現有買單不能假設取消或重複預留；外層batch gate不能被內層core_evaluation取代；等待資金不作已結現金。證據及結論在self-review.json。

FIRST在無continuation時只是明示合成帳戶起點聲明，不是個人完整前史認證；來源／宣告真偽、複雜分叉與完整退場再進矩陣仍未認證。已知B成交／委託／原持股則會阻擋偽FIRST。任意外部呼叫者若捏造整個新帳戶／省略歷史，並非本版通用認證能力；全部正式資格始終false。

外層classification／feasible_for_research才是完整研究閘門；core_evaluation保留原0.8對照。可行數量不代表途中風險已消失、保證退出或成交、最佳比例／獲利。初始buffer／edge／風險與計算預算都有明示研究來源／版本／可知時間；不把參照價差當預測。候選是同帳互斥替代方案，不是共用現金的同時委託。

未實作：最佳數量選擇、訂單／成交接線、R2/F、來源認證、自動解除衝突及原未支援帳務。未執行：bootstrap/hydrate、真實producer／資格重算、市場六方案／績效、UI／Android或樣本外；沒有來源新抓取或私人原件。1101 2026-01-02期初cash_claims維持帳戶阻塞UNKNOWN／拒算，不再為它搜尋公開資料。70／2／其中8／真實總淨合格0、主壓力null、正式action_resolution0.4、來源0.10及parents、圖形／人工基底規則保持。

一般工程／保存規則只整合原AGENTS／CONTINUE／capital_research README，沒有另一套工作政策。下一項建議（未啟動）：將最終數量候選閘門接到既有逐輪合成回放，集中驗等待／部分成交後重評，不自動選比例或勝者。無需使用者搬檔、提供私人文件或手動修程式。
