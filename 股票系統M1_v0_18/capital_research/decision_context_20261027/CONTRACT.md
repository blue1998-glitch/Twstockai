# 直接決策與完整續接數值環境定向驗證0.1

基線5f18238d6b2d2e1dec87da22d23a5bd3e1ff351a。僅確認core.decide及resume_decision兩個公開入口，續接包含bind_resume與checkpoint／原帳前置核對，不能只保護最後_decide。先存精確輸入、預期與來源版本／修前source，再實跑修前actual；重現才最小修復，不能重現則留反證，不修改oracle迎合推導。

重用quantity_context_20261027已保存完整合成回放的第0輪及第1輪execution_job原參數，直接呼叫決策函式，不重播該回放。第0輪取原decision_input；第1輪取原decision_input與完整continuation（previous_decision／checkpoint／cancelled_order_ids）。原資本2230、當期估值2226.660、reserve100、現金80及A10權利、A80/B7/C2與原兩筆fill／未成交歷史、latest及全部token原樣保留，不用終點相等代替完整核對。

預期decision直接取原execution.decision_records[execution.decision_id]完整原件。外層source_integrity_metadata按既有契約取原decision_input.source_integrity_metadata；resume另綁原checkpoint.integrity。這是事前明示的保存欄位投影，不冒稱原件另存過完整decide wrapper；不執行新正常決策來填oracle。input.json固定來源bytes／SHA／完整指紋、輪次、精確call參數與預期投影指紋，expected.json凍結規則與必要拒絕預期。

沿用既有五組contexts與preset／DefaultContext控制，完整輸出、decision_id、原帳與資格均應相同；不預定捨入控制一定重現差異。修前／後actual各存完整差異或精確原件投影參照、例外stack、source版本、呼叫端前後與input指紋。resume例外保存bind_resume／ledger／_decide呼叫計數，辨識是否在內部決策前中斷。所有舊actual／oracle／log／manifest及來源原件不覆寫。

若重現，只將兩公開入口的完整操作包在明示原標準Context：prec50、ROUND_HALF_EVEN、Emin=-999999／Emax=999999、capitals1／clamp0、空flags與InvalidOperation／DivisionByZero／Overflow traps，不繼承getcontext或DefaultContext。resume既有本體可純機械移至私有helper，以涵蓋前置核對；不改其驗證、tokens合併、計算、metadata或身分公式。implementation revision0.9.1，原decision schema0.8／同單0.9保持，不遷移或重算舊READ。

必要定向驗收：兩入口×五控制完整輸出／身分；同一原帳opening／fills／權利／reserve／latest／完整token與原本金不變；wrong-latest、checkpoint-token-change、reserve-drop、cash-right-drop、missing-checkpoint按事前預期拒絕，正常及preset都不能變成授權。正例input／caller保持，拒絕時也恢復caller；fresh程序修改DefaultContext，兩入口仍與原投影相符。純呼叫禁IO／網路／simulate／回放／Journal.save，原ledger核checkpoint可重用，不宣稱所有帳務函式0。只補一份既有候選入口的相依整合反例／正例核全文，不跑舊suite。

本輪只測這兩份schema0.8決策請求，不冒稱完整schema0.9同單重評或所有其他數值入口已驗。來源／圖形／策略／帳務公式及資格不改；原未支援帳務、R2/F、來源認證／完整分叉不擴張。1101cash_claims UNKNOWN、70拒算／2不足／其中8換股未支援／真實總淨合格0、正式false／主壓力null與全部parents保持。無真實producer、新行情／來源、九路徑、bootstrap／hydrate、UI／Android、樣本外、部署、交易、付費或訊息。Astra及救援原件未取得未讀。

原唯一Codex、原工作區／分支沿里程碑完成自審、必要驗證、正常commit/push及GitHub固定SHA讀回，不預設Work逐輪工程驗收。未定觸發、期間、金額、比例與風險取捨仍由Work及使用者決定。
