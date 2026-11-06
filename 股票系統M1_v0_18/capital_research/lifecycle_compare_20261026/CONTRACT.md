# 保存生命週期摘要唯讀並列 0.1

基線c1077952668b858ac745d29ea83a34f364dac577。唯一能力為驗證已保存結果的共同條件並並列原生命週期摘要；重用lifecycle.summarize_saved，不匯入／呼叫數值引擎，不重算帳、回放、評分或選勝者。無新比例、門檻、交易規則、UI或來源。

## 輸入與純讀取

純API `lifecycle_compare.compare_saved(request)`，schema=`capital-lifecycle-comparison-input/0.1`，固定schema、synthetic=true、items。items為2～8個固定label／saved_result物件；label非空且唯一，不含換行或表格分隔符。8為本版工程資源界線，不是策略條件；超限整次拒絕，不截斷。

saved_result須為原quantity_replay/0.1或conditional_quantity_review/0.1完整保存wrapper。先經原lifecycle只讀結構／指紋檢查；只有完整成功觀察至所載watermark的原結果才能並列。HISTORICAL_BEFORE_STOP、NO_SAVED_EXECUTION、UNREADABLE皆拒比，不把歷史帳當新成功結果。只有摘要而無原execution_job／tape的檔案不足以證市場環境，明確拒絕；不自動找最新來源或補tape。

CLI另負責讀檔，使用`python3 -B -m capital_research.lifecycle_compare_read 標籤=原件路徑 ...`；只輸出stdout，無RUN／寫檔／修復路由。-B避免Python生成bytecode快取。

## 共同條件

共同帳戶指同一比較起點的完整account及原帳opening（現金、實股、可賣量、一般reserve、應收應付／pending orders與cash／share權利），加上原資本。後來成交導致的期末現金／應付／持股差異是結果，不要求相等，也不把期末資本重設成期初。

起點decision_at／data_cutoff及最後observed_until／close available_at須相同；不自動截短到共同最短期間、不重建任意as_of。首個保存決策的當時可知layer1／layer2／fact_history／tokens及來源／基底／調整版本也要相同。原cost／execution／risk／scenario模型必須相同並在所有保存決策／attempt中保持原共同模型；不冒稱已支援不同風險預算的公平策略評比。orders、plans、重評次數、後續證據審查與成交可以不同。

共同市場使用比較窗口內保存的完整tape原列：at、available_at、code、price、capacity_shares、market_state、settlement_date、source_id、basis_id、version、qualification及其他已保存欄位，沒有只比價格的捷徑。跨輪按原序拼接，重複或倒序觀察拒絕，不合併容量。原ledger的來源／基底、窗口內quotes／calendar／events、coverage／qualification、terminal_costs及明示close proof也納入；缺資料拒絕，不補價、補零或自行制定交割日。

每個job須綁原ledger完整指紋、原decision／orders／observed_until及close proof。quantity結果須保存全部逐輪job，原前身checkpoint與前輪執行一致。conditional結果若只有last job而其continuation指向更早區間，未保存前身完整市場job時明示未支援；不能從fills或risk marks拼造容量／交易狀態。

比較範圍明列：窗口後的quotes／calendar／events／close rows只作完整性metadata，不使當期已知前綴失配；原opening權利即使未來到期仍完整比較。原coverage等其他metadata採嚴格一致，不聲稱全面未來中立。timestamp及數值字串本版用原canonical內容精確一致，不自動做時區／精度等價改寫。這是保守拒比，非策略門檻。

## 輸出

schema=`capital-lifecycle-comparison/0.1`。COMPARABLE才有columns及中文並列表：原提案／原單、已成交、活單、取消／到期、待交割／未知、預留、期末原帳與重評理由。某欄沒有該order時顯示「無此保存單」，不能補零或依股票代號強併批次。

不一致輸出REFUSED及每項差異的維度／JSON path與原值，columns=[]；缺provenance／版本／結構錯誤也拒比。先完整檢查，再最多呈現64筆差異；total_mismatches及details_truncated明示，顯示上限不影響拒絕判斷、不抽樣比較。各label原件digest、原execution／ledger完整ID及窗口identity分開保存；第一項只是相等性參照，不是策略基準或勝者。

ranking／selected_label始終null，所有正式資格false、主壓力null。COMPARABLE只表示保存的明示合成起點與窗口市場條件一致；不認證來源／實際成交，不驗證execution確實由該job計算、所有後續候選資訊完全相同或樣本外政策績效。原保存格式沒有整份job→execution的簽章，本入口保留此證明邊界，不重跑來補證。

## 證據與限制

先凍結原件路徑／bytes／SHA、精確變體規格、expected及本契約再實作。重用保存原件，結構變體僅測讀取防線，不冒稱新回放actual。必要驗收含合法等待／續用並列、期末結果可不同、容量／交易狀態／可得時間／來源／基底／交割錯配、起點／權利／截止、缺tape／只摘要、跨輪／前身、停止狀態、未知／損壞、資源限制、輸入不變及fresh-process禁止引擎／寫檔。無舊suite或producer重跑。

1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0、來源0.10全部parents、正式資格false／主壓力null保持。R2/F、信用、期初應付、外部活單完整重播、來源認證及完整分叉矩陣不擴張。無真實producer、UI／Android、樣本外、部署、交易、付費或對外訊息。Astra及第一工作區救援原件仍未取得／未讀。
