# quantity_replay數值環境隔離0.1.1

## 身分與本輪範圍

原/workspace/Twstockai、dev/m1-v018-chart-annotations，起始HEAD與遠端皆ea33452d9cc15c626b87748444a4b6377e3d84a3，tracked／index／untracked均0。僅原唯一Codex，沒有新分支、worktree或子代理。根四份最新有效接續沿用未變內容，補讀原回放契約與上輪數值隔離契約。

本輪授權只定向確認quantity_replay公開入口。先存契約、精確input／expected、五組Context、來源指紋與完整修前source，才執行修前actual。兩份新合成輸入只從舊seed更改研究parameter_source標籤，所有金額、單、價格、權利、來源／基底及日曆均保持；不回放後冒稱舊版本結果。其他engine、READ及策略公式不改。

## 實際重現與反證

原replay_sequence只有localcontext()及prec=50，仍繼承rounding、traps與Emin/Emax：

|修前環境|實際結果|
|---|---|
|正常／ROUND_DOWN|與新正常控制完整相同；保留為控制，不稱缺陷|
|ROUND_UP|完整結果不同；原帳scenario_net_return最後尾數由…97758變…97757，並改變相依保存身分|
|Inexact trap|decimal.Inexact例外，沒有完成輸出|
|狹窄Emin/Emax|decimal.Overflow例外，沒有完成輸出|

本例ROUND_UP的保存成交、現金及持股沒有改變，不把尾數差異宣稱投資收益影響。完整差異與原件在before及objects；沒有修改oracle迎合推導。

## 最小修復

只在公開入口建立完全明示、與原正常環境相同的Context：50位、ROUND_HALF_EVEN、標準Emin/Emax、capitals／clamp與traps／空flags。內部所有既有計算沿此local Context執行，退出後呼叫端不變。其他來源、條件、費用、會計或風險函式未改。implementation revision0.1.1，schema保持0.1；修後五組完整原始輸出與修前正常控制相同，含所有ID與來源metadata。

大輸出以objects/內容定址完整保存，同一內容只存一次；原始回傳物件的canonical JSON及簽章可核。before／after每筆actual各自有source版本，沒有將修前失敗或ROUND_UP差異覆寫成成功。

## 本輪實際驗證及資金／權利複核

5個唯一新測試方法、5次方法執行首次通過，不累加舊PASS、控制環境、子程序或案例。五組修前／修後確認之外，新增preset flags測試、舊觸發拒絕的正常／惡劣環境對照及一個新程序。所有回放都是本輪有限明示合成診斷；未跑舊整套suite或真實producer。

自審檢查不只終點：

- 首輪只有A20賣出／B7買入，後續獨立觸發B1，三筆fill ID唯一、第一輪fills／order_history是後輪精確前綴；不是提案A50／B20全數成交。
- 原資本2230不重設；首輪A80/B7/C2、現金1056.660，終點A90/B8/C2、現金1115.640、應計2225.640。
- 原現金應收80、待交A10各有一筆原journal到位，未消失、重複入帳或算成新收益。各輪checkpoint.row／accepted_fills／order_states與原execution完整相符。
- 各輪一般reserve100、latest decision/account與全部reviewed tokens相符，後輪保留前輪token；原origin ledger/account不變。全輸出逐環境核等，並非只核終點等式。
- 舊觸發追加仍NO_NEW_INDEPENDENT_TRIGGER／STOPPED_CANDIDATE_GATE，只有第一輪兩筆fill。停止前80現金權利與A10待交保留，沒有借context修復放行新批；歷史checkpoint仍不能拿來略過拒絕輪resume。
- 輸入與呼叫端prec、rounding、traps、flags、指數範圍等保持；新程序刻意修改DefaultContext/getcontext後仍得完整正常結果，禁止寫檔／網路，實際入口1次／simulate2次、評估及Journal.save均0。

本輪公開回放入口實際呼叫14次：修前5、修後5及四個直接相關測試呼叫，含2個修前例外；不是14個獨立市場樣本或14項測試。時序／未來前綴與READ接線未改，沿用既有保存證據，未重跑舊三種未來路徑、9路徑或其他已結清驗收。

## 未擴張與接續

獨立quantity_candidates.generate仍只有prec=50，若繞過回放入口其環境隔離未在本輪驗證；這只是下一個可定向確認的靜態疑點，不稱已重現。核心決策／execution／帳務直接入口也未宣稱全面修好。下一步可留Codex對獨立候選入口先保存反例再確認，有實際缺陷才修，不展開無限矩陣。

原外部活單／期初應付、信用、R2/F、來源認證與完整分叉不擴張；1101 cash_claims UNKNOWN、70拒算／2不足／其中8換股未支援／真實總淨合格0、正式資格false及主壓力null保持。來源0.10全部parents、正式action_resolution0.4、P0-3/P0-4及圖形／人工基底不改。

Work與使用者仍決定續抱／移轉觸發、期間、風險、金額及分批；待驗假說不接自動選擇／成交。Astra與第一工作區救援原件未取得／未讀，不推定890檔存亡。沒有bootstrap、新來源、UI／Android、樣本外、部署、交易、付費或訊息。原唯一Codex自審、正常保存與固定SHA GitHub讀回；使用者無人工操作需求，不要求Work重做工程驗收。
