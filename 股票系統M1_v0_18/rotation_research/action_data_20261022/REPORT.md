# 公司行動與逐日資金帳實測報告（2026-10-22）

本輪已完成獨立事件表、純數值帳、嚴格拒算、顯式帳戶比較、CLI保存／讀回及研究窗口資格核查。沒有改動原P1-7數字或生成新的策略成交。來源節點e3cadaf88ff6cf3a62374df262f73ad6b5a26c1a已推送、6檔GitHub原始內容逐位元讀回一致，收據source-checkpoint-readback.json。

## 官方原件及事件組件

|股票|交易所除權息日|已核每股現金毛額|公司預定發放日|其他證據／缺口|
|---|---|---|---|---|
|1101|2025-07-02|1|2025-07-29|淨扣款及實際入帳未知|
|2884|2025-07-22|1.2|2025-08-27|另有股票股利每股金額0.10015129；股數比率、可交易日未知|
|1101|2026-07-01|0.8|2026-07-28|淨扣款及實際入帳未知|
|2884|2026-07-01|1.4|2026-07-27|公司基準日7/7，不能當交易日|

events.json的五組件不是完整事件清單：四個現金股利組件及一個配股組件；四份原件的URL、SHA、擷取時點與每欄來源定位全部保存，公告原始可知時點null。2026交易所原件只至7/24，7/25～10/16未涵蓋；完整減資／其他行動登錄未取得。2025全年除權息列也不證明沒有其他類別公司行動。不得由除權參考價倒算配股比，或默認面額10元。

## 本環境實際執行

- 根bootstrap --hydrate-missing成功：0補缺、7差異保留，baseline_verified=true；current_tree_matches_baseline=false。不是沿用舊環境的準備成功。
- 新44個定向unittest全通過：6來源、31數值帳、7整合。tests.log保留完整名稱；不把舊18／9982／Chrome36計作本輪重跑。
- 122份原價量原件SHA／meta核對；重用原archive reader產出的輸入與舊generated/input.json、sources.json完全相同，兩股各317日期及兩筆null保留。未重跑舊策略研究。
- 對原計畫72組窗口逐一核查：70組有足夠保存筆數、2組40筆不足；70組每組都實際呼叫新核心並得到REFUSED，六方案均不計新總報酬，合格數0；沒有新排名或最佳比例結論。
- 三個明示工程帳務案例（現金含扣款、配股、減資）有完整逐曆日JSON及CSV。這些是人工工程測試值，不是補進真實行情、交易績效或來源證據。
- 四份真實毛額預定時程預覽保留真實收盤／缺行null，僅假設持有20,000股展示已知毛權利；例如1101 2026/7/1毛應收16,000至7/28按公司時程轉預定毛發放。淨現金、實際到款、淨值及總淨報酬均null，不表示使用者持倉或實際到款。
- 新CLI以獨立臨時目錄對工程例及真實拒算probe各RUN／READ；均逐位元一致。cli-verification.json保留長度、SHA、狀態。READ不import核心；同id不同內容拒絕且原檔不變（整合測試）。

## 錯誤及限制

首次來源builder把表頭當日期而ValueError拒絕；已僅篩格式正確的日期列，再從原件重建並驗值。沒有改原件或補事件值。

提交前git diff --cached --check發現標準CSV預設CRLF被視為尾端空白，並有一個新fixture檔尾端空白行；提交尚未發生。已明選CSV的LF換行、清掉空白行，未變動數字；重新封裝並在新目錄重驗。未出版的前一ZIP留在工作紀錄目錄，沒有覆蓋歷史交付。

唯一新增官方網路補查是玉山2025股東會紀錄PDF：Tunnel connection failed: 403 Forbidden，具體URL／時點在fetch-attempt.json。沒有下載到文件，不能稱其內容已核；沒有繞過、反覆請求，亦未重試舊除權端點。沒有證據可稱所有公司或交易所來源完全不可用。

真正總淨報酬比較仍未完成：完整公司行動、可核配股比／可交易及零股處理、投資人或明示稅費模型的淨分配、完整日曆與期初權利不足。原歷史公布可得、普通股主檔、Raw公司行動／五年Adjusted及SQLite根因未知保持。正式結構、交易資格、全換／分批、比例、觸發、投資飛輪未驗證。

新核心僅支持顯式成交及已結現金，不提供券商信用額度、未核同日淨額、合併／分割／認股或待入帳權利重疊處理；遇到此類情況拒算。指紋與資格旗標不替代外部原件驗證；完整欄位與報酬語意見CONTRACT.md。資料不齊先補來源，不把缺口轉成策略問題要求使用者猜。

本輪沒有UI變更或瀏覽器執行，Android仍NOT_TESTED_NEW_BUILD；未重開舊樣式／file://，未聲稱手機通過。舊頁可繼續使用，僅原本的條件式價格研究資格。原引擎策略、庫、歷史、舊頁及舊ZIP不變；保存核對見preservation-audit.json。未部署、付費、交易、發訊息或啟動子代理。

## 重現

在完整checkout先依根AGENTS bootstrap，然後進入股票系統M1_v0_18：

```bash
python3 -m unittest rotation_research.test_action_sources rotation_research.test_action_ledger rotation_research.test_action_integration -v
python3 -m rotation_research.action_sources
python3 -m rotation_research.action_study
python3 -m rotation_research.action_cli RUN --input rotation_research/action_data_20261022/real-input-probe.json --store /tmp/m1-actions-refused --id actual-probe
python3 -m rotation_research.action_cli READ --store /tmp/m1-actions-refused --id actual-probe
```

命令只改新action_data／指定新儲存目錄；不要執行舊study來取代P1-7交付。新下載包及實際解壓測試收據在deliveries/m1-actions-ledger-20261022/；包含可離線驗證的必要原件子集，非整個歷史專案。固定成品提交與GitHub逐檔回讀見其GITHUB_READBACK.md，收據本身在後續提交保存，不假造自指指紋。
