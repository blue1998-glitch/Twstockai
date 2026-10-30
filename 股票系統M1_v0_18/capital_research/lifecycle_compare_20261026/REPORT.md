# 功能交付：保存摘要共同條件檢查及並列

基線c1077952668b858ac745d29ea83a34f364dac577。本輪直接核對遠端／本地同此SHA、tracked／index／untracked皆0，祖先保留。新增lifecycle_compare.py及stdout-only CLI，重用未改lifecycle.summarize_saved；原核心、回放、帳務與所有舊原件不改、不重跑producer。

## 現在可用

可把保存的「仍等待重評」與「原單重評後買B20」放在同一表，先驗共同期初account／原帳opening／完整權利、起點與最後截止、當期已知初始候選環境及共同成本／風險模型，再驗完整保存市場路徑。成交與期末帳不同是結果，不要求相等，不重開本金。

tape的價格、容量、交易狀態、可得時間、來源、基底、明示交割日、版本、資格及額外欄位均參與比較。窗口內ledger quotes／calendar／events／close proof及來源metadata也綁定；原完整source ID與窗口identity分開。跨輪須保存全部市場job及精確前身，不能從成交或risk marks回填容量。只有摘要或前身市場缺失時拒比。

不一致顯示差異維度與JSON path，columns=[]；不把別的情境強列成同條件。label只是欄名，第一欄是相等性參照，不是策略基準。COMPARABLE才有原單核准量、成交、活單、取消到期、待交割／未知、預留、原帳與重評理由。沒有該order時顯示「無此保存單」，不補零；股票／方向明列，不藉同名order宣稱同一實盤單。

## 保存actual與必要測試

`after-final/summary.json`的21個凍結READ規格符合expected，僅4個可並列控制，其餘17個拒比；不等21個獨立市場樣本，也沒有策略排名。原件路徑／byte長度／SHA、精確JSON edit及expected在intake先存；unknown-capacity案另先存intake才執行。變體只是讀取診斷，不冒稱新執行器actual。

|案例|實際保存結果|
|---|---|
|wait-versus-reviewed|COMPARABLE。同一期初資本1330、一般reserve100、cash80／A10權利及1/9截止。等待欄B成交0／活單20；原單續用欄B成交20／待交割20。兩欄已結現金均596.500，應付0／401.400、原嚴格可用596.500／195.100分開，不評勝負。|
|same-document-control|相同原件兩個label可並列，只是同源控制，不成獨立樣本。|
|multiround-complete-job-control|兩輪完整job／前身／tape都在，原單7及新批1分開，原資本／權利／token沿舊摘要完整保留。|
|future-tail-outside-window|1/12未來價格不同、原ledger完整ID不同；當期1/9窗口identity與單量相同，COMPARABLE。不忽略期初即已存在的未來到期權利。|
|capacity-mismatch|原B20容量與B7容量不同，拒比，指到/market/tape/5/capacity_shares；沒有只看相同價格。|
|market-state／available-time／settlement-date|分別指到market_state、available_at、settlement_date並拒比。可得時間變體仍不晚於當下observation，沒有靠非法時序代替相等性檢查。|
|opening-capital／observation-cutoff|真實保存合成起點1330與2230、1/9與1/12截止不相同，明確拒比；不截短或重設本金。|
|opening-rights-tamper／cutoff-binding|改期初cash claim或job cutoff會先破壞原帳／決策綁定，拒比，不把它當另一份已執行合法帳。|
|source／basis-binding|外股來源／不同基底與原ledger不符，先拒絕，不只比價格。|
|unknown-capacity／missing-tape|UNKNOWN容量或缺tape拒絕，不補0或假定市場可交易。|
|stopped-result／summary-without-market|停止前歷史帳、只有摘要缺原市場來源都拒比。|
|prior-market-job-missing|conditional只有最後job卻帶continuation，沒有前身完整市場job，明示未支援；不從fills拼市場。|
|duplicate-label／resource-limit|拒絕重複label及9欄輸入；沒有覆蓋欄或截成8欄。|

`tests-final.log`本輪實跑11個唯一方法全通過；顯示補欄後只重跑2個受影響方法於tests-display.log，亦通過。實際方法執行13次，唯一11，不加21案例、初批讀取、舊13方法或歷史PASS。沒有失敗方法或改expected迎合結果。

專用方法另驗超過64筆差異仍拒比、總差異數及顯示截斷明示，並驗缺單顯示「無此保存單」；這兩項是測試斷言／log，不另冒完整保存比較案例。fresh-process CLI禁止引擎import、檔案寫入／刪改、子程序及網路連線仍成功，且與保存JSON完全相符；原input bytes不變。-B抑制Python快取，CLI沒有寫檔或計算路由。

initial原樣留史；加入跨輪close proof不可變防線後另存after-final，原source快照保留。最後只補股票／方向與核准原單量文字，views-final從既存after-final JSON產生；compare_saved及其前置邏輯bytes不變，未再比較／回算。source-versions-delivery明列此界線。合法跨輪close proof有控制例；違規跨輪close proof變更分支僅靜態防線，沒有新增專用逐輪反例，不宣稱完整時序矩陣通過。

## 自審與限制

唯讀來源共用完整起點與當期模型，原opening／權利／reserve／latest／tokens原樣保存。可並列也沒有合併欄位資金、下單、成交、來源認證或提高資格。比較採原canonical字串精確一致；等價時區／不同數字字串、metadata順序不自動改寫，可能保守拒比。coverage等metadata仍嚴格一致，不能說所有未來metadata變更都無影響。

原保存execution0.8沒有整份job→execution的簽章。此入口核對已保存job、ledger完整ID、原decision／order／clock與摘要結構，不重跑來證明job實際產生結果，也不全面認證來源或任意造假。後續每一時點的完整候選宇宙、相同實現曝險、樣本外時間切分、重疊污染、完整更正／分叉矩陣均未驗；COMPARABLE不是R1/R2政策績效驗收。

所有正式資格false、主壓力null；1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0及來源parents保持。R2/F、信用、期初應付及外部活單完整重播等原未支援不擴張。舊suite／九路徑／真實producer／資格重算／UI／Android／樣本外0。沒有新來源、私人文件、bootstrap、部署、交易、付費或訊息。Astra及第一工作區救援原件仍未取得／未讀，不冒Work獨立驗收。

## 下一項建議（尚未工程）

可留在Codex繼續：補C類「已核准事件追加單」的同單條件重評。必須沿原觸發核准、原order及剩餘量上限；新批仍要新獨立觸發，不能換family洗資格。這是既有規則的未接能力，不需發明比例或門檻；資金／token邊界列集中複核，仍不擴外部活單或其他帳務。
