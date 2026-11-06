# M-SCAN1｜11/3全市場逐股執行與保存結果開圖

**已完成1,986檔唯一掃描終態；1,955檔實際執行原核心，全部歷史不足；31檔來源拒用，工程失敗0。** 這是執行流程完成，不是充分多日圖形辨識或交易機會完成。

## 現在可以操作

原Cloud owner **http://127.0.0.1:8765/** → 首頁看掃描日期／母體／已執行／歷史不足／拒用／失敗 → 搜代號或名稱 → 查看價量與該股掃描狀態 → 查看圖形與判定。開圖讀保存的Journal結果，**不再呼叫辨識核心**，也不新增個股圖檔。原11/2、10/30獨立原圖與2～4股比較保留。

只綁原Cloud loopback，不是Android外連網址；手機尺寸模擬通過不等Android實機。沒有Oracle、VPN、外部部署、排程或交易。原憑證不變；同一owner程序受控重載一次，不是重啟Cloud。

|分母與終態|上市|上櫃|合計|
|---|---:|---:|---:|
|普通股母體／唯一終態|1089|897|1986|
|確實執行原core0.2／歷史不足|1082|873|1955|
|來源拒用，未呼叫核心|7|24|31|
|已有充分結構事實|0|0|0|
|工程失敗／未知核心結果|0|0|0|

只有一根已驗同基底K，不接未認證11/2或FinMind；MA／MACD暖機null，沒有突破、回測、失效、買賣、勝率或獲利結論。來源拒用的原始原因及null保留，不補價量。最新來源仍11/3，**本輪沒有抓11/4，也沒有完成11/4更新**。

## 如何重現與續行

未來工程仍必須使用原唯一Cloud與`codex/unified_workspace.py --environment-id <即時ID> --run ...`原工程鎖。日別執行入口：

```text
python3 -m graph_core.scan1_20261104.engine --as-of 2026-11-03
```

同來源／同版本再提交：已實測**0核心、0新紀錄、0檔案變動**，全批驗核約0.643秒。完整index與Journal不變。日期精確比對、不fallback、不抓來源；可指定`--work`指向下一個已合格交易日的獨立manifest。下一日必須先有合格來源／事實及明示版本，這個入口不自行取得、選新版或認證跨日公司行動。不是排程或已打通多日鏈。

- `prepare.py`：唯讀重核既存11/3六份官方原件／原CFI與ISIN母體，逐股對回既有原精度facts；只另存小manifest，0GET。
- `engine.py`：原Journal每股一份必要核心結果／來源指紋／版本／狀態；追加意圖／完成日誌並fsync。最多一個原worker子程序，原core0.2／參數／MA／MACD不改。
- 先受控停在23檔檢查點，再由另一程序續行；前23核心不重算，後段新核心1932，共1955。這是**真實檢查點停住與續跑**，不是宣稱實際SIGKILL復原測試。
- START後結果不明時不重算，記UNKNOWN工程失敗；半寫audit、損壞checkpoint或版本衝突保留並拒絕自修。單股worker錯誤可隔離為終態，其餘繼續；容量不足或無法安全判讀則停，不能保證任意破損都能無人工自動修復。
- `present.py`只把保存原結果接回原viewer，按原MA／MACD公式組裝單根顯示，不建立另一引擎。`provider.py`沿原owner／白名單／SHA／同源／RAM快取，連快取HIT也驗保存record；未知路徑與query拒絕。
- 前端以保存scan ID／record SHA配對原結果，技術ID預設收折。原raw fact的首次接件`analysis_status`未回寫；新掃描狀態另存顯示，不覆舊歷史。

## 實際驗收

**20唯一Python**＝10新執行控制＋3保存讀取＋7必要owner安全回歸；合成核心10次另列，不加到1955真實核心，也不沿用前輪20／29等數字。涵蓋逐股終態、來源拒用、檢查點續跑、零重送、未知attempt、worker隔離、SHA／版本／跨股錯配、半寫日誌及容量拒絕。

**33真實Chromium組／3精確JSON下載**：390直向、844橫向、1280桌面。全部1986分頁、可見掃描分母、上市2＋上櫃2真實輸入與保存結果、另不足及拒用、原兩日期開圖／比較、游標／移圖不跳分析日；無JS錯誤／外部請求。所有開圖新增核心0。新PNG只存私人Cloud，不公開受限行情。

完整讀回1986份Journal與來源綁定；1955份原K輸入fingerprint逐一符合原核心`source_prefix_fingerprint`。四個真實案例逐欄對官方原件OHLCV／股數／基底／結果ID，完整證據在Git外。7個實際owner HTTP安全控制仍401／403／404／405、HEAD不計算。

首次reader匯入漏了原src位置而失敗，未跑reader測試／未發布新頁；已保留修正前原碼與診斷，重用原src位置修正，沒有新增依賴或重算真實核心。最終20方法與33瀏覽器全部通過，不隱去中間整合失敗。原SIGKILL、Fontconfig、xref及其他UNKNOWN不宣稱修復。

## 實測資源

- 兩段有效掃描合計 **85.939秒**；含受控停住、換程序與檢查點驗證的首尾窗 **170.161秒**。worker程序wall合計79.425秒，和全流程耗時不同。
- parent OS ru_maxrss **337788KiB**，最大worker回報 **121288KiB**，分開列示；全Cloud合併峰值未測，不把它們相加或當Android記憶體。parent AS512MiB、worker AS256MiB／CPU3s／wall8s，每次批掃描上限600秒，安全停點可續。
- 新HTML **1967983B（約1.88MiB）**，初始零圖／零核心；已驗目錄下首次671～713ms、heap約4.35MiB。首次owner目錄重載約25.25秒另列。
- 原Journal約8KiB區塊／成功個股，僅必要原核心JSON／來源指紋／狀態；不複製全部歷史、原圖、1955張PNG／HTML或巨大市場JSON。原facts與6原件只引用。
- 摘要前FS淨增25378816B（約24.20MiB）、餘618303488B；最後文件／Git增量另記收尾資源。32MiB預算及512MiB保留通過，沒有需要升64MiB。不是未來每日永久容量上限或已驗備份。

## 保存與能力分界

|能力|狀態|
|---|---|
|全市場逐股執行|完成1986唯一終態|
|充分歷史的結構辨識|未完成，1955全為單根歷史不足|
|最新交易日11/4更新|未執行、不重試原端點|
|每日自動排程|未啟用|
|Android實機／外部入口|未測／未提供|
|正式策略驗證／自動交易|未批准、未啟用|

原source heads／FM3 90377 metadata沿有效SHA驗收不變，未重做約19GiB全量SHA；11/3舊頁、11/2及10/30原HTML完整bytes相同。僅推進原可變view指標，原bytes、argv與回復路徑另存；原1986終態／1946及1469舊圖全部保留，沒有清理、搬移或覆寫原件。原880 untracked保留。

來源0.10及parents、Raw UNKNOWN／正式false／主壓力null／估值null、全部策略及限制不變。全面持現仍主動候選，重新進場、錯過反彈與機會成本待驗，不批准觸發、比例或排名。獨立備份／重啟持久性UNKNOWN。

唯一本輪私人根`/workspace/twstockai-local-data/scan1_20261104/`包含manifest、results（原Journal）、attempts、complete-index、23檔及續跑收據、real-input-result-cases、verification、browser-final六張PNG／下載核對及service-current。服務PID由新service-current定位，舊輪PID留史。行情、完整核心、private manifest、PNG、憑證全部Git外；GitHub只程式、合成測試、不可還原摘要。

## 下一步只交Work用途驗收

```text
接續blue1998-glitch/Twstockai，dev/m1-v018-chart-annotations。以本目錄GITHUB_READBACK固定工程及最新遠端為準保留全部後續；先讀CONTINUE、PROJECT_VISION最新節及graph_core/scan1_20261104的README、summary、resources、verification、diagnostics、closing-resources與收據。
只做唯讀用途／證據驗收，不重抓11/3或11/4、不重跑1955核心／舊測試、不重啟服務、不開代理／Cloud／分支。
核1986唯一終態＝1955真實原核心執行且全歷史不足＋31來源拒用，失敗0；23檔檢查點後另一程序只跑1932，重送及新頁開圖核心0。33瀏覽器／20 Python是本輪實跑，不加舊批或10合成核心。
原owner只Cloud localhost8765，可搜股看實際狀態、保存圖／不足說明、舊兩日期及比較；Android外部入口／實機、11/4更新、多日充分結構、每日排程及正式策略均未完成。
若Work讀不到原私人Cloud／PNG／完整Journal，明列未取得／未讀，不把公開摘要當已驗原件，不要求使用者手機搬檔。
只回報用途差異與下一個主要缺口：合格多日同基底歷史／公司行動連續資格。保留主動持現及重新投入機會成本需求，不自派新來源／部署／策略工程。後續工程只由此原唯一Codex接受總監明確派工。
```
