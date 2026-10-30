# 獨立期初權利證據缺口檢查 0.1：本輪實際結果

最低基線／起始遠端／本地 HEAD：75cada894fa85f5b66dcb69f4e7e5c4ceb0b724b；原分支 dev/m1-v018-chart-annotations，原工作區 /workspace/Twstockai。起始 tracked 修改0／index0／untracked0。只原唯一Codex，無代理、worktree或新分支；本輪沒有commit/push授權。

## 實際完成

新增純核心 `capital_research/opening_evidence.py:check` 及獨立證據目錄；既有資金框架仍0.8、來源catalog仍0.10及全部parents。沒有接到真實來源資格或帳務，不建立第二資金帳。不必提供私人帳戶資料。

先保存 CONTRACT、fixtures、22案input／expected、intake與舊檔指紋，此時 checker 檔案尚不存在（intake記錄）。實作後另存5份source版本，才執行新診斷與定向測試。沒有修前缺陷聲稱；這是新能力的合成契約驗證，不是既有真實拒算解除。

本輪只執行一次新測試集合：**21個唯一方法全部PASS**；含subTest不另計。22組fixture逐一生成保存actual，全部符合事先保存oracle；22不是新增方法數、不是獨立市場樣本或績效。歷史13／22／24／25等PASS不累加，舊suite／真實producer／資格重算／六方案／UI／Android／樣本外執行0。沒有失敗回合或改oracle。

## 保存actual及限制

所有精確輸入／預期／實際在 `cases/案名/{input,expected,actual}.json`；整體指紋與核對在 `summary.json`。共15案GAPS_PRESENT、1案ASSUMPTIONS_PRESENT、6案STRUCTURALLY_COMPLETE_NOT_AUTHENTICATED；後者仍可包含明示未支援帳務。

|驗收|保存案例及實際結果|
|---|---|
|未知／來源零值／假設分離|empty-is-unknown與missing-is-unknown仍UNKNOWN；sourced-zero為SOURCED_ZERO_DECLARATION，但opening_entitlements_verified=false；hypothetical-zero僅HYPOTHETICAL_ASSUMPTION|
|身分不可借用|wrong-account_id、wrong-scenario_id、wrong-code、wrong-price_source_id、wrong-basis_id、wrong-adjustment_version均UNKNOWN／EVIDENCE_SCOPE_MISMATCH；不因value同為[]放行|
|完整性與內容|incomplete-zero缺完整未結項聲明；content-conflict的證明值與欄位值不同，兩者均UNKNOWN|
|起日前權利|prior-right-without-holding：1101實股／可賣均0，仍保留2025-12-15取得的9元應收、2026-01-08宣告支付日；不入帳，不計可用現金|
|可得時間|late-proof：1/5可得的證明不能用於1/2決策；equal-timezone-boundary：同時可得及等價時區一致；captured_at不替代available_at|
|未知不補值|unknown-net-and-pay-date保留淨額／支付日null；unknown-share-dates保留交付／可交易日null；future-entitlement不能當期初權利|
|未支援能力|nonempty-payables、nonempty-pending_orders、fractional-right保留原值並明示重播NOT_IMPLEMENTED；不把形式完整當帳務可執行|
|重複身分|duplicate-right明確列DUPLICATE_ACCOUNT_ITEM_ID；不默默去重或入帳兩次|

另有新方法驗證：未知來源時間／缺定位、非整股／NaN／負值／float、不完整月份、真實入口／假VERIFIED／無時區／倒置截止拒絕，及輸入不變／結果決定性／全部正式false。這些方法中的變體沒有各自完整cases actual，證據屬測試原碼與 `tests-final.log`，不冒稱都有獨立保存JSON。

## 真實窗口仍拒算

既有 `rotation_research/subsidiary_proposal_20261023/window-qualification.json` 的1101／2884雙向、2026-01-02～01-09、5交易日窗口仍含OPENING_ENTITLEMENTS_UNKNOWN，daily／journal空、總淨null、original_numeric_replay_called=false。舊 `action_study.py` 明寫空清單不是零權利證據；舊 `action_ledger.py:71` 的拒算條件不變。

日期角色：真實帳務起點依舊契約是1/2收盤；本輪fixture所有16:00等時點明示合成，不是認證真實市場／券商日終可得時間。1/9不是可回填期初資訊的時間。來源後來擷取與當時可知獨立；本模組只檢查聲明一致性，不能證明聲明真實。

目前沒有為這兩個窗口取得任何「已認證零權利」。有來源零值聲明與真正驗證完成分開；全部外部資格false、主壓力null、舊70拒算／2不足／其中8換股影響未支援／真實總淨合格0不變。這些是舊保存狀態，不是本輪producer重跑。

## 保全及未完成

既有tracked檔案與index全部不變；`preservation-before.json` 保存9個核心／入口／窗口檔指紋，`tracked-index-before.json` 保存原5257個tracked索引身分。另以原Git blob核對來源catalog與原碼，見 `preservation-after.json`；不要求歷史封存source等於現行source。新manifest只列本輪新增檔案，不覆寫任何舊manifest／oracle／log／actual。

未實作：來源認證、私人資料入口、真實一月精確可知時間認證、完整行動／權利盤點證明、實帳接線／重播、資格升級及原所有未支援帳務（含信用、期初應付、不中斷外部既有單等）、R2/F。不聲稱排除任意偽造或所有複雜權利。

未執行：真實producer、來源擷取、舊suite、結清0.8／第58頁重查、市場六方案、UI／Android與樣本外。Astra與第一工作區救援原件仍未取得未讀，不等待、重建或推定890檔存亡。正式action_resolution0.4、來源0.10與parents、P0-3/P0-4、reaction_facts及人工基底契約全部保持。

使用者本輪無需人工操作或提供文件。Work尚未取得未提交原件，本報告不是Work獨立驗收。下一步如要讓Work讀原件，由原唯一Codex另獲保存授權後正常commit/push並讀回；不需使用者搬檔。
