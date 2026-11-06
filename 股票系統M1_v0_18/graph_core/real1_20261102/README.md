# M-REAL1｜真實全市場私人研究工作台

**FM3已保存資料已接通UX1搜尋、OBS1雷達、COMP1同期比較。** 不重抓歷史、不呼叫核心／指標、不重新生成原圖；原始行情與完整成品均留Git外。資料截止 **2026-10-30**、普通股參照來源日期 **2026-11-02**，不是新的交易日更新或正式可交易訊號。

| 已保存狀態 | 本輪接線核對 |
|---|---:|
| 全部普通股參照／終態 | 1,986 |
| 多日研究／歷史不足 | 1,439／30 |
| 品質拒用／缺分析日行情 | 514／3 |
| 可按需讀取原圖（包含30短史） | 1,469 |
| 當期原候選事件筆數／涉及股票數 | 16,954／1,049 |
| 正式交易訊號資格 | 無；原false／null保持 |

1439＋30＋514＋3＝1986；「其他517」指514＋3，不再加算30。歷史不足依原當期可比段資格，未必只有一根K。事件是保存候選的path記錄，同日多尺度／多候選不等獨立型態、股票、反應或交易訊號。

[真實接線摘要](real-integration-summary.json) · [全部HTTP讀回](route-verification.json) · [手機尺寸驗證](browser-verification.json) · [空間實測](storage-measurement.json) · [原件保護](source-preservation.json) · [原核心／指標不變](protected-source.json) · [測試及失敗範圍](verification.json) · [失敗與修正](FAILURES.md) · [固定GitHub讀回](GITHUB_READBACK.md)

## 實際私人入口

本原Cloud本機：**http://127.0.0.1:8765/**，原M-MOB1 owner驗證服務，只綁loopback。入口已用真實資料與owner登入驗證；無登入401、錯Origin403、非白名單404、寫入405。不是手機可從外部連線的網址，沒有新公開入口／Oracle／VPN／PWA或部署。Cloud退出後服務是否仍存在不保證，Android實機仍NOT_TESTED_NEW_BUILD。

私人連線資訊／owner憑證選擇器：`/workspace/twstockai-local-data/real1_20261102/connection-private.json`；只由此唯一Codex或已授權的本機操作者讀取，**不要分享或推GitHub**。密碼不寫入命令列、報告或本README。owner-auth.json沿原scrypt格式，不覆寫先前憑證，服務不記Authorization／個股請求紀錄。

完整成品與接線收據：`/workspace/twstockai-local-data/real1_20261102/integration-first-private.json`，內有精確preview.path／SHA。實際成品位於同目錄`artifacts/<build_id>/market-real1-v01.html`；經原DU2 codec還原原bytes，不能把.logical路徑不存在當成遺失。私人PNG在`browser-first/`；沒有把真實PNG、行情、圖表分片或完整分析放上GitHub。原FM3根完整保留。

## 操作流程

1. owner登入後搜尋代號或名稱；市場／原狀態篩選、每頁50、全部1,986檔可翻頁。拒用與缺行情保留原因，不用別股舊圖代替。
2. 開個股，沿原K／量／MA／MACD與來源證據；廣角、局部、移圖與觸控查詢不改分析截止日。下載JSON仍是原完整核心、K及指標。
3. 「雷達」預設當期首次可觀察日。股票數與原候選事件數分開；發生日、確認日、首次觀察、批次日期及停止／不可比資格各自保留。只索引明示當期，沒有宣稱完整歷史雷達。
4. 搜尋或雷達明示加入2～4股→「比較」。可移除／替換及返回原圖。不同日期、RAW／還原、缺資料或短史拒比；同日但期間／來源／公司行動未知只描述並列，不排名、不認證跨基底等價。

原FM3 summary的67次請求／30次核心等current_run欄位屬其歷史最後一批，原樣保留於original_saved_summary；不能當本輪計數。本輪來源請求／辨識／指標重算均0。原全部來源0.10及parents、Raw／公司行動／歷史可得／SQLite UNKNOWN、正式false、主壓力null不變。

## 接線與空間

新`graph_core.real_workbench`只讀原Journal與已保存圖；使用原event_radar與stock_comparison投影，不建第二套算法／資料庫。原HTML的payload／Canvas／指標部分逐bytes保留，只替換既有工作台addon。原market_preview.build不執行，因此不重寫1,469份圖表。

原圖以同檔案系統hardlink在**新Git外目錄**建立1,469個只讀服務別名，SHA／bytes／inode相同；不複製約3.30GiB原圖內容。別名不是獨立備份，不得在檔案系統直接寫入別名。原文件內容、mtime、mode、inode與路徑不改；nlink增加1469有明確紀錄。

完整比較投影邏輯JSON約1.74GiB，以既有DU2無損codec另存壓縮片段，不具現化每份大JSON。手機只按需讀一份原圖及該股證據；比較最多保留4份精簡投影，不載全市場歷史。HTML約19.40MiB，包含全名單與當期雷達及一份原圖初始化資料，不含全部1,469份行情。

成果目錄實際新增 **195,633,152 bytes（186.57MiB）**；含owner設定、8張私人截圖、log及驗收收據的整個私人工作目錄在量測時新增 **197,505,024 bytes（188.36MiB）**。按唯一新增inode及directory配置區塊量測，排除共享的原分片；不是用包含hardlink原payload的普通du數值冒新寫入量。量測時點／剩餘容量見storage-measurement。預留512MiB，容量不足拒絕，不清理原件；跨檔案系統拒絕隱式複製。

## 本輪驗收

- **16唯一Python方法**＝9新增接線＋7直接受影響owner安全回歸，最終通過；不累加前兩批或舊PASS。
- 新loader合成控制驗證來源／股票／基底／日期／結果／原分片SHA綁定、篡改拒用與舊版相容；原共同comparisonScope正反控制通過，不新增規則。
- 真實1,469分片全部SHA、解碼K、完整core、MA／MACD逐值等於原Journal；1,469比較及雷達投影沿原helper，索引拒絕0；其他517保留原拒用。
- owner服務**2,939份實際GET**：1,469原圖＋1,469證據＋HTML，全長度／SHA相同；串流驗證不保存5.06GiB傳輸payload副本。
- 320／390直向、844橫向及1280桌面，**29組檢查／8完整下載**通過；四尺寸都逐頁核全1,986身份，含真實上市／上櫃、四股同期比較、短史拒比、原缺值／基底旗標、雷達回原圖、拒用不露舊圖及HTTP篡改控制。JS錯誤0、外部請求0。只是Chromium工程測試，不等Android實機或辨識品質驗收。

## 可重現入口與停止

由Codex先依M-UNIFY1即時核環境及鎖，之後在「股票系統M1_v0_18」執行下列程式；不要求使用者手機開終端或搬檔。

```bash
python3 -m graph_core.real_workbench --source <已核FM3根> --output <同磁碟Git外新父目錄> --audit-manifest <M-PORT1私人完整清單> --receipt <Git外新收據>
python3 -m unittest graph_core.real1_20261102.test_integration graph_core.mob1_20261102.test_private -v
node graph_core/real1_20261102/test_loader.cjs
node graph_core/real1_20261102/test_real_ui.cjs <私人connection.json> <Git外新驗收目錄>
python3 -m graph_core.real1_20261102.verify_routes --config <私人connection.json> --report <Git外新報告>
```

同一原件／程式綁定的已完成build只讀回原成品，不重投影或新寫圖。不同版本另存，原件或binding錯誤／缺失明確拒絕，不修來源。驗收程式所需連線配置含私密資訊，不進Git；登入服務沿`graph_core_chart.mobile_private`原CLI，尚未進行外部正式部署。

此里程碑工程及真實整合完成後停止。仍缺Oracle帳戶、已授權持久私人磁碟與足夠容量、獨立備份／重啟復原驗收、具認證私人HTTPS入口及Android實機。不得把hardlink／同overlay新目錄當備份；不啟排程、交易、付費、外部主機或新研究。
