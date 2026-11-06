# 明示減碼／退出里程碑報告

基線：`da8a9bf4e95898c6e9d95369c8cbc141b27bfe74`。原工作區 `/workspace/Twstockai`、分支 `dev/m1-v018-chart-annotations`，唯一既有 Codex；固定交付提交由 Git 記錄及本輪回覆提供，不把自引用 SHA 填入 oracle。

## 新增能力與最小差異

只修改 `cash_action.py`、`cash_action_execution.py`：新增顯式 0.2 SELL 行動／執行契約。舊 0.1 HOLD／BUY 保持。由原 checkpoint 導出完整帳戶，僅減少指定 code 的目標股數，經既有 `core.resume_decision` 檢查；不改費稅、帳務、風險、不交易區間、成交、交割或事實歷史公式。原 `execution`、`continuity`、`execution_continuation`、`action_ledger` 等 source 指紋保持。

執行綁完整 action／checked／原帳／close proof，全文重驗後只接受核准股票 SELL、總委託量不超過核准量。退出是意圖；結果仍以真正 fills／剩餘委託判斷。其他持股與現金／股份權利不能省略，原 origin／本金／general reserve／latest／全部 token 不重設。

## 凍結及恢復

先保存契約、精確 input／expected、77 項凍結指紋、17 份保護原件與兩份舊 source 快照。舊 API 的修前 actual 拒絕新版本；此項是缺少能力，不宣稱既有財務公式有錯。

首次套 patch 時執行環境連線中斷，該 patch 沒有寫入。原環境恢復後先唯讀核身分、remote／HEAD／index、77 frozen／17 protected／兩個舊 source，確認原件完整後才接續。診斷另存，不重建凍結材料、不重跑舊 producer。詳見 `diagnostics/environment-recovery.json`。

## 實際驗證

23 組事前凍結案例均符合預期 status／reason／simulate 次數；7 組合法執行各使用原 simulate 一次，其餘主反例 simulate 0。另存錯股票委託控制，在 simulate 前拒絕。案例、控制與回歸不是獨立市場樣本，也不加進測試方法數。

本輪實際執行 8 個唯一 unittest 方法，全數通過；`tests-final.log` 保存完整輸出。沒有失敗後改 oracle，未重跑整套舊 suite、九路徑、市場六方案、真實 producer、資格重算、UI／Android 或樣本外。必要相容性只針對三份既有 0.1 保存結果（HOLD、新獨立 B20、舊觸發拒絕）作完整比較，全部相同。

| 驗收 | 保存證據 | 支持範圍 |
| --- | --- | --- |
| 明示減碼、指定股退出、拆單 | `initial/reduce-B3`、`exit-B7`、`split-exit` | B3／B7 及逐 fill 費稅；不選數量 |
| 無成交／部分成交 | `initial/limit-down`、`capacity-zero`、`empty-orders`、`partial-exit-B20` | 跌停／容量／空單不冒退出；部分7、剩13保持 |
| 原帳／權利／一般預留 | `test-evidence/continuous-origin.json`、`daily-handcheck.json` | 原本金1180／reserve100、80現金權利／C2股份權利、原 fills／orders／fact／latest／9舊token |
| 應收與交割一次 | 同上及 `controls/partial` | 逐日現金與應收分開，1/12一次入帳；每日日帳會計等式 |
| 部分賣出後續播 | `controls/partial/comparison.json` | 與同 root 一次完整執行的明示觀察、每日日帳、完整 execution／checkpoint 相同 |
| 防錯綁及越界 | `initial` 對應拒絕案、`controls/wrong-order-code` | 超賣、假減碼全退、退出量錯、非整股、錯latest／基底、活單／應付、非checkpoint、重標真實、BUY／別股夾單、超量拆單、改checked、交叉版本 |
| 原不交易區間 | `initial/existing-no-trade-band` | edge=0 仍拒絕，不為 SELL 擅改風險／政策 |
| 持有／賣出與加碼分離 | `controls/not-new-capital-qualified` | 新資金不合格不等於不能檢查減碼；沒有批准下一筆買進 |
| 未來與數值環境隔離 | `controls/future`、`controls/context` | 未來 evidence 不改當期 research；完整性 metadata 可不同。兩組惡劣 Context 下完整結果相同、caller／DefaultContext 不變；API無 IO／網路／quantity生成，input 不變 |
| 舊版相容 | `controls/legacy/summary.json` | 三份原保存 0.1 完整結果相同；不宣稱全舊 suite 重跑 |

## 可獨立核對的數值

主要帳起始現金 858.86、B7／C2、現金權利 80／C2 股份權利。SELL B3：`3×19.98−1−1=57.94`；1/9現金不變、應收 `80+57.94=137.94`；1/12現金 `858.86+80+57.94=996.80`、B4／C4。SELL B7 淨137.86，終1076.72／B0／C4。分3＋4兩 fill 費稅各1，總淨135.86，終1074.72。原買進費用留在原帳，不重新扣作賣出回本門檻。

部分分支起點是另一份完整已結清的原 B20 checkpoint，現金598.6。退出20但容量7，只成7，B13／C2、應收217.86、現金仍598.6；原單剩13延續。1/12只交割與到期，現金 `598.6+80+137.86=816.46`、B13／C4。原完整 path 有1/12空日宣告，不把沒有 tape 推定為沒有其他成交。逐時比較只涵蓋明示觀察點及日終，不宣稱任意未記錄時刻已驗。

## 保持的限制與後續

新決策仍須已結清／無活單／應付且原帳完整。原未完成單先沿既有續播；本輪不新增取消策略或買賣觸發，不把 BUY 的新資金資格放寬。未知權利、不支援限售、信用／外部既有單缺完整歷史、R2/F、來源認證、複雜分叉及市場回放仍拒絕／未實作。合成結果不證明市場績效、策略勝負或正式圖形通過。

原1101期初cash_claims UNKNOWN，70拒算／2不足／其中8換股影響未支援／真實總淨合格0、正式 false／主壓力 null、來源0.10及全部parents、P0-3/P0-4／reaction_facts／人工基底保持。Astra、Work原研究文件與第一工作區救援原件未取得未讀；不認定890歷史檔已取得或遺失。

本項自審完成後按既有授權保存，GitHub讀回另核固定提交原件；無需使用者操作。下一項只核已有已定義優先順序，尤其完整合成行動帳能否直接沿既有全帳評估口徑；若無已定義缺口就停止，不增重複 READ 工具，不先制定市場政策。
