# M-PROD-CORE1｜Twstockai 正式版每日分析主線

原Cloud同一個owner入口 **http://127.0.0.1:8765/** 已實際運行正式產品頁。這是Cloud內部位址，Android外部仍`ANDROID_EXTERNAL_NOT_CONNECTED`；不是可從手機點入的網址。本輪不再把附件／Oracle阻塞當內部產品工程前置。

首頁直接顯示資料日期、每日分析結果、最新接件限制、全市場搜尋與市場／狀態篩選。選股後看精確OHLCV、原保存核心判定與按需互動圖；換日期可回11/2、10/30及原2～4股比較。11/3只有單根合格K，**歷史不足**；MA／MACD暖機null，不產生突破或買賣結論。

## 真實完成範圍

11/3全部1986唯一終態：上市1089、上櫃897；1955份原核心結果（上市1082、上櫃873）經新流程驗證重用，31來源拒用（上市7、上櫃24）。本輪真實核心新增呼叫0、重算0，沒有冒稱1955份新多日圖。完整來源→原始欄位→保存fact→原core/Journal→正式owner頁已實際跑通。

11/4新接件使用**11/5的新日期化attempt**，未重試舊DAILY-CHAIN1 attempt。官方順序4次GET，前3完整；第4上櫃行情HTTP200但body不完整，保留原件片段後停止，後2未請求。新日`BLOCKED_SOURCE`，原11/3有效head及正式頁保留。原件／HTTP／安全headers／時點／SHA／partial診斷全在Git外；見不可還原的[source摘要](source-verification.json)。同attempt重送只讀既存拒絕，GET0，不重新判日期或繞過來源。

## 單次執行入口（工程維運，不要求本人開終端）

先用當前Cloud工具核實環境身分，再沿原`codex/unified_workspace.py --environment-id <本輪實際工具ID> --run ...`持有唯一工程鎖。以下Python模組以既有`股票系統M1_v0_18`及`src`作PYTHONPATH，沒有新相依、bootstrap或第二服務：

```text
python3 -m graph_core.prod_core1_20261105.flow run --date 2026-11-03
python3 -m graph_core.prod_core1_20261105.flow fetch --date YYYY-MM-DD
python3 -m graph_core.prod_core1_20261105.flow status
```

`run`重核指定保存日六份原件、普通股身分、精確fact與版本，續行原scan/Journal，完成後啟用同一owner正式頁；相同輸入重送0核心／0新增成品。`fetch`只接受台北日期之前、官方實際證明的閉市日；同一日期attempt有持久接件／失敗檢查點，不盲重試。操作員經授權可加`--attempt 明示新名稱`，只為未完整傳輸開獨立新attempt；同名稱仍零GET，原attempt永不重寫。曾有401／403／429或轉址拒絕時，改名／換日仍在GET前拒絕，需先審查而非繞過。完整新日若通過原source gate，沿原parser→單日新段→原逐股core/Journal→小型正式頁；**不是認證跨日接續**。單股錯誤、未知中斷及容量防線沿用原scan。未完成逐股批次不發布；完成計算僅寫prepared head，owner經原認證與白名單就緒後才提交product head。啟動失敗回到原owner argv，保留所有原件及前批。

原FM3／11/2／10/30長史仍保留；歷史銜接沿用HISTORY-BRIDGE1已結清證據，缺區間價基底／公司行動與時點證明，不偷接、補價或倒填可得時間。未新增來源0.11、catalog、策略、金融引擎或資料庫。

## 驗收與資源

[summary.json](summary.json)、[verification.json](verification.json)、[preservation.json](preservation.json)、[tests.log](tests.log)均為本輪精簡證據。12唯一Python方法、26實際owner瀏覽器流程群（390／844／1280），不累加中間8／9／10或舊套件。真實兩市場各2股精確OHLCV／核心輸入／圖核對；拒用、舊圖比較、刷新、401／403／405／404／HEAD控制通過。兩市場合成來源成功路徑與中斷續跑另測，不冒真實新日成功。新程序讀回與同源重送PASS；沒有重啟Cloud，不能證重啟後持久性或獨立備份。

本輪首頁1,956,605 bytes；瀏覽器首次載入828／805／830ms（各一次本機量測，非Android網路性能），JS heap約4.4MiB。真實流程來源／結果讀核約3秒，含受控同owner重載的總耗時另記summary；最終協調器peak約112MiB。核心worker沿原256MiB AS／3s CPU／8s wall，掃描600s上限；協調器CLI512MiB AS，原512MiB磁碟安全保留及32MiB本輪預算。不複製19GiB原件，實際新增／餘量見summary，全部私人行情、圖與完整Journal在Git外。

失敗紀錄：真實新接件`INCOMPLETE_RESPONSE`已保留且未重試。Python中間8／9／10及最終12均PASS，沒有虛構測試失敗；發布兩階段與設定回滾是本輪實作時的靜態安全補強。原SIGKILL／Fontconfig／xref等歷史不宣稱已消除。

## 唯一下一優先路徑

讓本人手機進入**這套正式產品**，不再另做預覽：只提議原Cloud連入本人免費私人Tailscale網路，以Serve私人HTTPS轉送既有loopback8765並保留owner驗證；不開Funnel／公網、不搬FM3、不新增OCI權限。仍需本人一次批准該私人網路連接與第三方免費方案條款，並先核平台確實支援及方案資格。**本輪未安裝／登入／啟用，沒有已驗網址，也不保證Cloud支援**；若平台不支援，須總監另定承載權限，不能偷偷換成公開通道。

正式交易策略、資金比例、全面持現金的觸發／重新進場與機會成本仍待驗證批准；每日自動排程未啟用。Oracle／橋接本輪不動。固定工程及原bytes讀回收據另存`GITHUB_READBACK.md/json`，避免自指；完成內部產品交付後停止。
