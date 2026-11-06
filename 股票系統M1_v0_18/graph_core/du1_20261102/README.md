# M-DU1｜增量工程完成定向驗證；真實新交易日仍受阻

本原工作區的FM3私人根實際可讀；f2f96c16的「另一可見檔案系統缺根」紀錄保留在下方與原preflight.json，不作本環境現況。最新收尾見 [REPORT-current.md](REPORT-current.md)、[本輪數字](summary-current.json)、[來源擷取](source-attempt.json)、[保全／容量](preservation-current.json)。

已沿原Journal／core0.2／指標／M-G3／M-MOB1接好：單次日更新、同源重送零重算／零成品寫入、逐股檢查點續跑、明示修訂留版、驗證／預覽失敗不發布新head、私人批次選擇與既有服務讀取新head。全體參照不靜默消失；沒有新行情者或轉板未知各有終態。新官方日與原歷史保留為**分段**；公司行動與跨來源可比性未知時重新暖機，不認證連續完整帶。

**本輪真實新增股票／新交易日套用／真實新日分析均0。** 六項官方請求僅各一次，TWSE仍10/30，TPEx日線IncompleteRead；五份完整原件與失敗收據留Git外，未重試。11/2名冊上市1089／上櫃897共1986全部留BATCH_NOT_APPLIED診斷，沒有把它們稱為1986次新核心分析。新source不足時保留最後10/30的1469圖。

27唯一Python＝18新增＋9必要回歸，28合成Chromium／16精確下載、6原真實圖抽查／4精確下載。合成新日與原10/30真實抽查分開，不冒新交易日或Android通過；[初次失敗](tests-initial.log)和[最終方法清單](tests-current.log)均保存。

原私人根約20GiB、目前可用約2.8GiB；本協調器保留全批新結果／預覽的metadata保守預估約17.8GiB。這不是實際新日寫入量，現環境未有足夠預估容量；已加容量拒絕與檢查點保護，不刪唯一資料。overlay持久／獨立備份／重啟復原仍UNKNOWN。

[單次設定](execution-config.example.json)供未來已核Oracle私有持久主機接手，**未安裝或啟動排程、未建主機**。Python入口 `graph_core.du1_20261102.run_once` 自原fm3-continuation取種子，使用既有daily.lock，完成結果與預覽／批次目錄讀回才更新current-increment-run。M-MOB1 `--head` 可讀最新已完成目錄，不需重啟該服務。

現有真實圖仍由原fm3-continuation的preview.path定位；沒有新增可由Android直接開啟的安全網址。新實際批次不存在，不能展示假11/2圖。所有真行情／完整結果／HTML／PNG／憑證在Git外；本目錄只程式、合成控制及不可還原證據。來源0.10／parents、正式false／主壓力null及所有缺口保持，不重跑帳務／市場策略或M-FM3歷史補建。

本輪以PARTIAL_REAL_NEW_SESSION_BLOCKED結案。Oracle帳戶、持久容量、獨立備份與私人手機HTTPS入口暫停，使用者明確表示帳戶辦好後才交總監接續；不因這次工程驗證而自行部署或開下一里程碑。

---

## 下方為f2f96c16舊環境前置紀錄（原文留史，不代表當前原工作區缺檔）

# M-DU1｜原私人歷史不可存取，工程未完成

本輪不是全市場更新完成。原程式已安全快轉至 `933212b829e91516dc13db918d05eac59c3d9688`，原分支且起始工作樹乾淨；但目前可見檔案系統沒有 `/workspace/twstockai-local-data/fm3_20261101/`。原續跑狀態、runs、原件、請求額度收據、檢查點、histories、results與preview均不可讀。

[實際核對收據](preflight.json)記錄逐項路徑及時間。只在/workspace、/tmp、/mnt作有限目錄查找，找到的FM3／MOB1目錄都是Git內程式／摘要，不是私人行情庫。未見活躍FM3／每日更新worker，沒有啟動另一個。可見FM1／FM2私人資料不等於FM3完成版，不以舊資料或新下載替換。這不證明原資料在其他Cloud／平台備份已遺失；其全局存亡與恢復位置未知。

## 保留的既有成果

FM3 completion/summary.json仍保存1986檔終態、1439多日（TWSE938／TPEx501）、30短史、514拒用、3缺行情、1469可開圖、待處理0的歷史收據。上述數字只屬既存交付，**不是本輪原件獨立核對或即時狀態**，沒有回退成193檔或重新補建。

已讀最新根規則、FM3完成摘要、MOB1 README及daily_update、market_daily、market_finmind、market_preview和mobile_private相關接線。現有process明確拒絕跨producer接續；缺原FM3依存時，不能假包成官方來源，也不能以空Journal推定從未取數。沒有刪拒絕條件或修改公式。

## 本輪實際完成／未完成

只完成版本同步、原環境檔案與程序核對、阻塞保存。API0、核心0、測試0、新增圖0；沒有產品源碼變更。**M-DU1增量實作、合成替代驗收、真實11/2更新、前後批指紋、手機新批載入均未完成／未驗**，不能把診斷稱為新增更新能力。

沒有執行capture／prepare／replay或重新下載1986股；沒有重啟環境、建立替代FM3目錄、搬資料、部署或排程。沒有以暫存副本冒充持久庫。正式false、來源UNKNOWN、主壓力null及既有拒算保持。

## 恢復條件及Oracle邊界

必須先由平台恢復／重新掛接原私人檔案系統，或提供已授權且完整可驗的私人備份，再核原批ID、Journal封套、原件SHA、檢查點、額度收據及預覽依存；之後仍由本唯一Codex沿本輪原授權完成M-DU1。僅GitHub程式／摘要無法還原受限行情。未找到原資料前，不做跨來源拼接、不反覆取數或擴建架構。

不要求使用者下載、上傳或搬來源檔，也不要求指定新策略。本輪保持BLOCKED，所需是原私人資料存取恢復，**不代表必須先開Oracle**。Oracle帳戶、持久磁碟、常駐排程、固定Android入口仍暫停；本輪未申請或啟用任何服務。原始受限行情與可還原結果未進公開Git。
