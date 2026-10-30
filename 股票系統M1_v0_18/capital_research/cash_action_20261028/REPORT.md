# 明示現金行動受控接線0.1：自審報告

最低基線d77c244d122af879b84cd85d6a9f7ac3aea0149e；本輪開始local/ref同SHA、工作區乾淨，保留先前4個目標文件提交與所有祖先。只新增cash_action.py與本目錄；根既有四接續及capital README增補進度，下方歷史原文保持。原quantity/core/execution/continuity/ledger/fact/eligibility與market_case_v2原件全部未改。

## 已完成能力與證據

原quantity入口正持股限制不再阻擋**明示行動**：不經數量搜尋，只把HOLD或單股BUY_FROM_SETTLED_CASH傳到原decide／resume。開新假想帳只是明示研究假設，不等投資人帳戶。續接必須完整checkpoint，從原帳取得現金、shares、應收／待交股份、reserve及latest，透過原完整source/fact/attempt歷史傳遞token；不收手填帳／token或任意family/targets覆寫。

FIRST_ENTRY重用quantity已核的episode歷史核對；退出A後A=0仍可證曾持有，假首次外層REJECTED且candidate_ids空。真正重入固定C，舊／共柱／跨股事件不通過，獨立新事實通過。首次B可以用有效原B-event作當期review，不強迫改名或創新事件；曾用過該股票則不能靠改family／新review重置批次。外層及core診斷分開保存。

原帳準備明示本金2180＝現金1000＋A100×10＋C2×25＋現金權利80＋C2股份權利×25；reserve100不能花。賣A100的合成成交價9.990，沿原整元進位費1、稅3，應收995；1/8現金仍1000，995及80應收另列，C2待交權利保留。1/12才現金2075、C4，原始本金仍2180，沒有重開帳。A20部分賣出後A80／剩單80仍保存；本入口遇活單明確NOT_IMPLEMENTED，不虛構撤單或釋放預留。

31個有限行動正反例在after-final/summary.json全符合凍結input/expected。7個唯一測試方法、7次執行、首次全過；根summary/actual為初版診斷而非另一套PASS。指定原來源／舊證據保護指紋及全部凍結輸入保持。額外缺token／改opening反例與較晚可知close另存test-evidence，未累加方法或控制數。

當期future-revocation-prefix的整份research與無未來撤銷正例完全一致，完整輸入fp不同保留於metadata；可知撤銷案例仍拒絕。重用既有惡劣Decimal控制及正常控制，完整結果一致、caller/DefaultContext保持。opening純呼叫禁IO／網路／simulate／replay_sequence／generate／ledger；checkpoint續接的原ledger驗證必要，不冒全部ledger0。新行動沒有委託／成交或帳戶posting；precondition的4份合成執行只是測例準備，市場回放0。

## 保存與初版診斷

先凍結CONTRACT與precondition input/expected/source，再建4份原引擎checkpoint；31份action精確input/expected於adapter實作前凍結。初版手算把稅2.997漏進位，原件/frozen保留，另有expected-fee-rounding.json援引既有fees函式的ROUND_CEILING及獨立算式，沒有改帳務或31案資格oracle。初版source完整留diagnostics/cash_action-initial.py並核root source-versions SHA相符。自審把完整輸入移出research後另存after-final，不覆寫任何初版actual/log。

保存採既有里程碑授權：只原分支正常commit/push及固定SHA GitHub逐檔讀回；不部署／付費／交易／訊息、不開代理／分支／worktree。最終SHA及讀回摘要由對話回報，避免為回填提交本身建立循環提交。

## 尚未完成／未執行／不足

- 未實作：本入口到委託／數值執行協調、八行動完整dispatcher、整張域／多股最適化、活單／期初應付／限售釋放完整重播、R2/F、來源認證、自動更正／解除衝突與完整分叉矩陣。
- 未執行：②真實市場回放、真實producer／資格重算、舊suite／九路徑、市場六方案、樣本外、UI／Android。新資料擷取0。行情／權利未知不補造，沒有1/13行情或第三輪成交證據。
- 仍不足：Work v0.24/JSON0.16原件、Astra及第一工作區救援原件未取得未讀；僅依使用者摘要。1101期初cash_claims UNKNOWN、來源0.10全部parents覆蓋／淨額缺口、70拒算／2不足／其中8換股影響未支援／合格真實總淨0保持；正式false／主壓力null不升。
- 不能證明：策略有效、最佳比例、提前退出優於續抱、真實市場可成交或全帳真實績效。現金買進增加曝險仍由現行core風險檢查，與賣A籌資分開。

## 下一步分工

若繼續工程，最小獨立里程碑是把本輪已明示、通過的行動接至**既有合成執行**，只接受外部明示原單與同一完整日曆／tape，沿原帳續接並保留未成、部分成交、費用／交割；尚未授權或實作。這不依賴最佳比例，適合原Codex後續有限工程。市場②的本金、股數、減少比例、預留、共同期間、風險／政策及成交模型仍由Work與使用者確認，不為市場回放猜值。無人工操作或搬檔需求。
