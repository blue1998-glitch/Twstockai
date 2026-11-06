# C原單重評與一次再評外層數值環境驗證0.1

基線c8d95bca07057b05f038ca1c906635331ba2e0df。只直接確認conditional_quantity_review.reassess_conditional及conditional_retry.retry_rejected兩個既有公開外層，重用已保存精確input／expected／actual。先凍結來源指紋、預期與兩份修前source，才執行修前actual；實際重現才最小修復，不能重現則留反證，不改oracle迎合推導。

主例：c_order_review_20261026的valid-C-same-order（最終after-checkpoint-fix）及c_order_retry_20261027的qualification-restored（最終數值initial）。只讀原cases/input.json及expected.json，全文actual為原oracle，不重建fixture或更改研究參數、行情、容量、單、數量、基底、時點或來源。沿用quantity_context_20261027五組contexts及preset／DefaultContext控制。

兩入口有既定相依：retry會用original_input呼叫一次reassess；reassess會委派原quantity回放核原批准，再委派原simulate。這些是所選請求的必需內部工作，明列呼叫數，不冒稱producer／simulate為0；不另啟舊build、整套suite、九路徑或真實producer。

若重評入口重現，先只修該入口，再以after-review-only保存retry同一主例的五組actual。只有retry在子入口修好後仍因自己外層污染，才修retry；若全部相符就不修改retry，保留反證。after-review-only與before留史，after才綁最終source，不混用版本。

如需修復，只固定各公開完整local Context為原標準prec50、ROUND_HALF_EVEN、Emin=-999999／Emax=999999、capitals1／clamp0、空flags與InvalidOperation／DivisionByZero／Overflow traps。重評implementation revision0.2.1、再評0.3.1；原review schema0.1／0.2／0.3、decision／execution0.9、checkpoint0.8保持。不改內部本體、原單／remaining／family／觸發、帳務、資格或任何下游公式；舊READ不重算或遷移。

必要回歸只選既有六案：重評UNKNOWN、重評部分7後已知撤銷取消13、重評錯原單、再評UNKNOWN、再評部分7後餘13到期、再評錯前身。before／after各normal及preset，全文及身分與原件相同，遭拒仍遭拒、不升資格。原資本1430、reserve100、原帳opening／權利／fills／pending及剩餘／latest／完整token保持；retry保留第一次REJECTED receipt，再加當期結果，不重開本金。續用原單20的剩餘量，不變新批；新批仍須獨立觸發，不新增1/13行情。

保存每次完整差異或精確原件path／bytes／SHA及完整結果ID，錯誤含stack／source版本／實際呼叫數；caller與input前後指紋保持。相同大型JSON直接引用原件，不截斷或覆寫舊actual／log／manifest。fresh程序修改getcontext與DefaultContext後仍全文相符，不寫檔／網路／Journal.save；純呼叫IO與兩入口preset另驗。

只跑本輪唯一必要方法，選定案例／前後控制／子程序不累加成PASS或獨立市場樣本。原lifecycle READ必仍純讀且可讀保存結果，不新增READ工具。未測完整C矩陣、來源更正／完整分叉、所有未來路徑或任意數值域，不宣稱策略或市場績效。

1101 cash_claims UNKNOWN、70／2／其中8／真實總淨合格0、正式false／主壓力null、來源0.10全部parents／action_resolution0.4／P0-3／P0-4／reaction_facts及人工基底保持。R2/F、信用、期初應付／外部活單、來源認證、自動解除衝突等原未支援不擴張；Astra及救援原件仍未取得未讀。

原唯一Codex、原工作區／原分支沿里程碑必要實作、自審、正常commit/push及GitHub固定SHA讀回；不開代理／worktree／分支。無bootstrap／hydrate、新行情來源、真實producer／資格重算、市場六方案、UI／Android、樣本外、部署、交易、付費或訊息。未定策略由Work與使用者決定，不預設逐輪Work工程驗收。
