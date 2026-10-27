# C兩公開外層：定向重現、分步修復與自審

## 身分、來源及範圍

原/workspace/Twstockai、dev/m1-v018-chart-annotations，起始本地HEAD及遠端均c8d95bca07057b05f038ca1c906635331ba2e0df，tracked／index／untracked皆0。只有原唯一Codex，無代理／worktree／新分支。

先存CONTRACT、精確input／expected／actual來源、兩份原source與指紋，再實跑。主例直接取c_order_review_20261026/cases/valid-C-same-order/input.json及最終after-checkpoint-fix原件，另取c_order_retry_20261027/cases/qualification-restored/input.json及最終數值initial原件；沒有重建fixture、換parameter_source、重編日期或價格。正常結果與原件完整相符，預期不是由本輪正常RUN後填入。

另選六個直接相關原案例：重評UNKNOWN、重評部分7後取消13、重評錯原單、再評UNKNOWN、再評部分7餘13到期、再評錯前身。只用這八個保存請求，不跑完整舊14／17案矩陣或舊suite，各次環境為獨立診斷，不加總成持股、現金或獨立市場樣本。

## 三階段actual及最小修復依據

|階段／主例|normal／ROUND_UP／ROUND_DOWN|Inexact控制|狹窄指數|
|---|---|---|---|
|before重評|完整相符|完整相符|Overflow|
|before再評|完整相符|Inexact|Overflow|
|只修重評後的再評|完整相符|Inexact，自己最終checkpoint|Overflow，自己前置checkpoint|
|after兩主例|每組完整相符|完整相符|完整相符|

修前十控制七相符、三例外；不把沒有重現的捨入或重評Inexact控制稱為缺陷。before的再評Overflow可由未修子入口傳出，不能直接推定兩個外層各需修；故先只固定重評，另存after-review-only五組再評actual。

中間版本的retry source指紋仍等於修前，review指紋已是修後；retry仍在自己的修前conditional_retry.py:78 make_checkpoint(origin,old,...)出現Overflow，以及:158 make_checkpoint(origin,actual,...)出現Inexact。stack不經_reassess_conditional，當時simulate分別已完成2／3次，證實子入口修好後仍需第二個獨立外層保護。中間actual及兩份版本照留，不混作最終source結果。

只改兩檔Decimal import、implementation revision及各公開local Context：明示prec50／ROUND_HALF_EVEN／Emin=-999999／Emax=999999／capitals1／clamp0／空flags／標準InvalidOperation、DivisionByZero、Overflow traps。兩個內部本體原樣，core、execution、quantity、ledger、數量／family／資格／帳務／風險／成本公式全部不改。revision分別0.2.1／0.3.1，所有原schema保持，舊READ不重算或遷移。

after十組主結果及result指紋均精確等於原actual；必要邊界十二組亦完整相符。before邊界normal六組相符、preset兩個早期錯身分停止相符，其餘四組被Clamped遮蔽；after恢復原結果。UNKNOWN仍拒評、部分單仍接受其原限定範圍而餘量取消／到期，不能將十二組泛稱十二個拒絕。

## 必要測試及額外資金／原單複核

六個唯一方法、六次執行首次通過：三階段／來源版本、原單及帳戶歷史、選定六邊界、preset純呼叫、兩個fresh程序、既有lifecycle READ相容。沒有數值測試失敗或中間批重跑；不累加歷史PASS、前後控制或子程序。主控制前後20次、中間5次、邊界前後24次、preset2及fresh2，共53個頂層有限請求；retry內含review等呼叫另明列，不加為新測試／獨立樣本。

- 同一原r1-B、original_order_quantity20、remaining20、C family與B-event觸發保持；review_decision.new_evidence_tokens=[]。只續用原單剩餘量，不換family／ID或把舊事實變新批；新批獨立觸發規則沿既有未改source，未新跑批次producer。
- 原資本1430、一般reserve100、original ledger／opening、prefix fills／order_history、權利／order_states／latest及全部reviewed tokens照原件。各B fill均映射回原r1-B，fill ID唯一，沒有再造本金或第二帳，也不只看期末等式。
- 重評主例原單B20後，1/9仍有現金80及A10待交，purchase_payable401.400、settled_cash596.500、available_cash_strict195.100；權利／應付不提前結清。其原帳部分A50賣出仍原1/6、B20買入原1/9且沿明示1/12交割，不把核准當保證成交。
- 再評從另一份已保存的拒評原件出發，不把重評成功主例當其父。保留原REJECTED receipt及其decision／fact source，新增ACCEPTED receipt；原被拒decision不進accepted decision_records，不升latest。新review前身精確接原latest，原單／tape前綴／模型／完整token不變；期末原cash275.100、A60/B25/C2、待交權利與應付按原時程結清。
- UNKNOWN兩例沒有B買入；重評部分7後13按原已知撤銷於1/12 09:01取消，at／observed_at保持；再評部分7的13按原期限到期，非無條件假定買足20。partial與各成功主例的截止決策相同，後續成交／容量不同，不倒灌未來結果為新決策。
- 錯原單／前身仍STOPPED_INPUT_ERROR，未出execution或宣稱成交。所有外部資格false、主壓力null，研究／資料／交易資格分開。
- fresh每例都含原核准重建：review1、quantity_replay1、generate1；重評simulate2／ledger34，再評retry1及simulate3／ledger66，Journal.save0。原公開函式就是合成RUN，不能把這些必要內部呼叫冒成0；沒有另開舊build／suite／producer。fresh監看禁止寫檔與網路，input／caller／DefaultContext前後相同。
- 原lifecycle READ在禁所有數值引擎／回放下仍READABLE，與讀原件的完整摘要相同，原result不變；沒有新READ功能或隱式遷移。

## 保留邊界與下一步

只驗所選schema0.2／0.3的八個保存請求及原控制，未重跑legacy0.1 B/E、整套C矩陣、完整分叉／來源更正、所有未來路徑或任意數值範圍。未擴「一次再評」限制、再評啟動前限制的NOT_IMPLEMENTED、外部活單／期初應付／信用、R2/F、來源認證或自動解除衝突。獨立全換、直接checkpoint／ledger及舊trend入口仍不能稱全面隔離。

1101cash_claims UNKNOWN、70拒算／2不足／其中8換股未支援／真實總淨合格0、正式false／主壓力null、來源0.10全部parents、action_resolution0.4、P0-3／P0-4、reaction_facts及人工基底保持。Astra及第一工作區救援原件未取得未讀，不推定890檔已取得或全遺失。

無bootstrap／hydrate、真實producer／資格重算、市場六方案、九路徑、新行情來源、UI／Android、樣本外、部署、交易、付費或訊息。原唯一Codex沿里程碑自審、正常commit/push及GitHub固定SHA讀回，無人工操作，不預設Work逐輪工程驗收。未定策略仍由Work與使用者決定，這些結果不證策略或市場獲利。

下一項可留Codex，僅唯讀收斂剩餘獨立全換／checkpoint／ledger／舊trend入口是否仍影響現行明示合成研究流程，重用既有盤點與本輪覆蓋，不逐helper盲測；沒有可達的實際缺口就停止同類修補，不為續作虛構功能。
