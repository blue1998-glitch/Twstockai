# 結果與自審

## 實際修前、修後

基線 `9efc3f34ae46df21411ef738a57d61c2fca7a540`，正確原分支、乾淨工作區開始。只從 quantity_context_20261027 的兩份既有完整結果取出精確請求及原 generation，不重跑舊回放、不新增行情、來源或研究參數。控制直接重用舊 contexts.json 及 test-controls.json 的固定指紋版本。

| 原請求 | 正常／向上／向下／Inexact 控制（修前） | 狹窄指數（修前） | 五組修後 |
| --- | --- | --- | --- |
| initial，第0輪 | 四組完整相符 | Overflow，無結果 | 五組完整相符 |
| old-trigger，第1輪 | 四組完整相符 | Overflow，無結果 | 五組完整相符 |

「完整相符」是完整 JSON 及 generation 指紋相等，不只股數或候選個數；actual 用來源 path／bytes／SHA、round_index 與完整結果指紋精確指向既有原件。差異結果原本規定獨立內容定址保存，本例沒有不同的完整成功輸出。每筆都保存當時 production 指紋、呼叫端前後狀態、輸入指紋與例外。before 原樣保留；after 才綁修後 source。

## 最小修復

只改 quantity_candidates.py 的 Decimal import、implementation revision 及 generate 的 local Context。舊版只指定 precision=50，仍繼承指數範圍等環境；現明示 Context(prec=50, ROUND_HALF_EVEN, Emin=-999999, Emax=999999, capitals=1, clamp=0, flags=[], traps=[InvalidOperation, DivisionByZero, Overflow])。與既有標準回放環境一致，不修改任何下游公式、列舉順序或資格／帳務。implementation revision 0.2.1；原 0.1／0.2 schema 不變，保存結果無隱式遷移或 READ 重算。

## 權利、資本及候選

initial 原 A100/B0/C2、現金1000、reserve100，含 A10 待交及80現金權利。四候選仍為續抱、A50/B20 部分換股、指定 A 退出留現金、A0/B94 全換；最後一個只屬 WAIT_SETTLEMENT_REASSESSMENT，不是立即可買。

old-trigger 原 A80/B7/C2、現金1056.660、reserve100；完整帳戶及 continuation 與請求不變。checkpoint 的原始本金2230、原帳 opening／已保存 fills／權利／未成交狀態、latest／完整 token 沿既有接線核查，沒有另建帳。B8／B94 增加候選仍因 NO_NEW_INDEPENDENT_TRIGGER 拒絕，不能藉數值環境變更、family 或舊事實重評繞過新批要求。當期估值2226.660與原始本金2230分開；不以終點相等宣稱中途資金無重用。

## 必要測試與診斷

五個唯一方法：修前／後完整輸出、候選及帳戶接續、preset flags／traps／無 IO、搜尋上限拒絕、fresh 程序 DefaultContext 隔離。首次四通過、一個新測試斷言失敗；保留 tests.log、原測試 source 及原 oracle 指紋後，只修當期估值／原本金混用的斷言，只補該一方法通過。最終五唯一方法通過、六方法執行，不把子程序、20組前後控制、讀檔或舊5／8／其他 PASS 加入計數。

fresh 程序直接 generate 一次，simulate／replay_sequence／Journal.save 各0，監看禁止寫檔與網路；實際 DefaultContext、呼叫端及輸入不變。continuation 核 checkpoint 可重用原 action_ledger，不宣稱所有帳務函式呼叫0；不是新成交或新帳務重播。搜尋上限反例事前凍結，只改 max_grid_combinations=0，仍明確拒絕且候選空，無默默抽樣。

## 邊界與下一步

只驗兩份已保存 schema0.2 請求及原控制，沒有重跑全部 schema0.1／舊 suite、完整分叉矩陣、九路徑、真實 producer／資格重算、市場六方案、UI／Android 或樣本外。不宣稱全面隔離所有其他公開數值入口，亦不把合成穩定性當策略有效或市場報酬。

所有來源 parents、action_resolution0.4、來源0.10、P0-3／P0-4、reaction_facts 與人工基底保持。1101 cash_claims UNKNOWN、70拒算／2不足／其中8換股影響未支援／真實總淨合格0、正式false／主壓力null不變。R2/F、信用、期初應付／外部活單、來源認證、自動解除衝突等原未支援不擴張。Astra與第一工作區救援原件未取得／未讀，不推定歷史890檔存亡。不 bootstrap／hydrate、部署、交易、付費或發訊息。

下一步可留原唯一 Codex，一次唯讀盤點尚未隔離的公開數值入口與既有證據，只列實際有限缺口，避免逐 helper 無限擴張；若沒有具體缺口就停止。策略仍由 Work／使用者決定。本輪不預設 Work 逐項工程驗收。
