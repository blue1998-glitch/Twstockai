# M-GRAPH-LAZY1｜按需開圖，來源不足明示

已接入原11/3價量頁的「查看圖形與判定」。不是全市場每日自動掃描。

## 實際操作

原Cloud本機 owner：**http://127.0.0.1:8765/**，沿用原登入。搜尋股票→查看價量→查看圖形與判定→返回當日價量；可換回11/2、10/30原圖及原2～4股比較。首頁1986身分不計算；1955可用日K、31來源拒用仍分開。

**本來源只能證明11/3單根可比K。** 新舊來源／公司行動尚未認證連續；沒有把舊圖拼成新日完整圖。原core0.2實際回傳「歷史不足」；顯示真實單根K／量，MA／MACD暖機值為null，不產生突破、回測、失效或買賣建議。舊圖另開，日期不改。最小缺口是可驗證的多日同基底連續資料與公司行動／來源銜接資格；本輪停止擴張演算法。

這不是Android外部網址。Android實機NOT_TESTED_NEW_BUILD；外部入口、Oracle、排程、獨立備份及重啟復原尚未核實／啟用。

## 範圍與保全

同一Cloud、工程鎖、/workspace/Twstockai與原dev分支。原0.2核心、MA／MACD算法、P0-3／P0-4、來源0.10／parents、策略／帳務／資格不改。未抓行情、未批次重算1955檔、未複製19GiB或既有原圖。兩原source head相同；90377原路徑metadata沿有效SHA驗收，不重做全量SHA。原880 untracked保留。

原owner程序只受控重載一次，同8765、同憑證、loopback；舊argv／控制指標bytes另存，可逆。只追加新HTML、私人action manifest與新UI catalogue；原頁／分片／prepared-state／行情／source head不覆寫。不是Cloud重啟或外部部署。

## 實作

- `worker.py`：唯一純數值子程序，原core0.2＋原MA／MACD，只接受已核單日段，無行情IO。
- `provider.py`：已驗owner白名單內的固定action，核原件／股票／ISIN／CFI／來源／RAW基底／日期／程式版本；拒絕任意路徑、query與未知action。
- 原`mobile_private.py`在既有認證／同源／Host檢查後，選配上述provider；沒開此選項時維持原行為。HEAD不計算。
- 原LITE viewer接線，不新增圖形引擎或另一網站。前端核回應SHA、identity、日期、fact SHA及原結果binding。
- RAM LRU最多8股／2MiB、TTL600秒；來源／版本不符拒用且清快取。同一已驗快取HIT零核心、零持久檔；過期重算。單一計算、每分鐘最多12新工作是工程資源保護，不是策略門檻。
- 每股子程序AS256MiB、CPU3秒、wall8秒、輸出256KiB、禁止檔案寫出；忙碌429、來源／資源不符409。沒有無上限磁碟圖形快取。

## 本輪實測

20唯一Python（13新＋7必要owner回歸），27次純合成核心呼叫，真行情不計在單元測試。29最終Chromium組／3精確下載，390直向、844橫向、1280桌面；上市2＋上櫃2真實來源精度、另1不足及1拒用、舊兩日期圖與2股比較均驗。7實際HTTP安全控制與2次重開HIT；重開零檔案變動、零新核心。

真實owner核心共5次／5股，另1次同首股獨立資源探測，不是6獨立市場樣本。中間桌面腳本誤用tap失敗及修正留史；中間21組不與最終29累加。無Android實機／辨識品質／策略勝負驗證。

首次4股點選225～247ms，快取重開111～123ms（含瀏覽器互動）；直接HTTP重開40～46ms。owner子程序回報峰RSS97348KiB，獨立探測12288KiB另列，不能以較小值代替服務實測。HTML1585132B，初始零計算，已驗目錄後頁面648～688ms／heap約4.5MiB；首次owner目錄重驗另約24.27秒。建殼約0.11秒，不當核心加速。

摘要前FS淨增6066176B，餘658534400B；16MiB預算、512MiB保留均滿足。後續文件與Git收尾容量另記`closing-resources.json`，不是未來每日用量外推。詳見resources／verification／failure-diagnostics／tests.log。

## 私人成品與重現

所有實際行情、完整分析、PNG、憑證、action manifest、可還原UI都在Git外：
`/workspace/twstockai-local-data/graph_lazy1_20261104/`。

- `browser-final/graph-390.png`、`graph-844.png`、`graph-1280.png`、`old-2026-11-02.png`、`old-2026-10-30.png`：最終實際畫面；`browser/`保留中間失敗。
- `browser-config-private.json`、`service-current-private.json`：新服務PID／原登入選取器。原LITE connection的舊PID留史，不用它當目前PID。
- `build-private.json`、`actions-*.json`、`source-state-private.json`、`verification-private.json`：精確來源／程式／路由／保全收據。
- `first-worker.stdout-private.json`、`tests-private.json`、`browser-final/verification-private.json`：實際結果與計數，不公開原始內容。

工程入口均需先通過根AGENTS的唯一環境／`codex/unified_workspace.py --run`鎖。`build.py`及`activate.py`是首次接線程序，既有完成收據存在時不得盲目重建或重載；`verify.py`是本輪有界核驗，結果不可變，重驗須另存新紀錄。單元合成fixture同樣不可覆寫；未來重跑需獨立測試輸出目錄。版本指紋改變會拒用舊action；新來源／程式版本必須另建經審核manifest，不放寬原限制。

## 下一輪只交Work唯讀用途驗收

```text
接續blue1998-glitch/Twstockai，dev/m1-v018-chart-annotations。
以本目錄GITHUB_READBACK.json的固定工程與最新遠端為準，保留全部後續，不寫入／bootstrap／重抓／重算／重啟服務或另開代理。
先讀根CONTINUE、PROJECT_VISION最新節及graph_core/graph_lazy1_20261104的README、summary、resources、verification、failure-diagnostics、closing-resources與固定SHA收據。
核「查看圖形與判定」已接原11/3價量頁，但只核實單根真K／量與原core歷史不足；不要稱完整新日結構、自動掃描或正式訊號完成。31來源拒用與舊11/2、10/30圖分開。
若可讀同一原Cloud，沿原owner登入及本目錄列明私有畫面／紀錄唯讀看用途差異；原圖／行情／憑證不得公開或轉交未授權第三方。若Work不能讀私人Cloud，明列未取得／未讀，不把公開摘要冒原件，不要求手機搬檔。
沿本輪20 Python、29最終瀏覽器、7HTTP控制及2重開證據，不重跑或累加中間組。Android、獨立備份／持久性及外部入口未驗保持。
驗收：一眼見歷史不足與來源斷點、可返回價量與獨立舊圖／比較；新資訊不冒新訊號。只回報具體用途差異與最小資料資格缺口，不派無限補研究或擴張算法，不自行啟下一里程碑。
```
