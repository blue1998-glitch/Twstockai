# M-PROD-DAY2｜傳輸修正已接正式入口；新日仍來源受阻

同一正式產品仍運行 **http://127.0.0.1:8765/**（Cloud本機，非Android外部網址）。本輪沒有預覽、第二網站或新交易日上線。11/3全部1986終態、1955歷史不足／31來源拒用保留；沒有重跑原全市場核心。正式頁讀到本次11/4接件失敗與精確原因。

## 實際傳輸診斷與停止

舊上櫃HTTP200宣告5,329,099 bytes，只有4,570,729 bytes，JSON停在字串中途，舊拒用正確。Issue #5授權的**唯一新whole-GET attempt**仍HTTP200，只收到1,015,401 bytes，短少4,313,698；8.660秒即EOF，沒有碰180秒或16MiB程式上限。新舊ETag、宣告長度相同，新partial與舊partial前綴逐byte一致。這能確認HTTP framing不完整，**不能確認是官方origin、CDN、代理或哪個socket節點造成**，也不能宣稱舊檢查誤判、縮小讀取已修好供應商。

三份完整舊原件依URL／長度／SHA重用，原時點不改；新GET只有上櫃1次，後兩分類原件0次、不重試、不Range、不換主機路徑。只有上市完整來源可核到11/4，上櫃partial不採用、不解析成行情。六份／兩市場閘仍不通過，11/4正式新結果0，原11/3有效head及FM3保留。詳見[summary.json](summary.json)、[verification.json](verification.json)。

## 真正修正的程式

原正式入口`graph_core.prod_core1_20261105.flow fetch --date ... --attempt ...`仍沿原`daily_chain1_20261104.intake.run`，**現已委派本目錄transport.receive**：原URL／原proxy／TLS、單一GET無轉址、64KiB有界read1、Content-Length精確核對、原HTTP chunk解析器終止檢查、未證framing與非預期encoding拒用、硬180秒牆鐘、partial長度／SHA／缺口／HTTP時點完整留證。原socket35秒限制及原32MiB總body／16MiB每body上限沿用，不放寬日期、原parser、CFI、價基底或公司行動資格。明示custom opener的read hook保持相容。

本次限定修復入口：`python3 -m graph_core.prod_day2_20261105.capture --date 2026-11-04`。只能原唯一Cloud經`codex/unified_workspace.py`持原engineering.lock執行；它重用完整3件、只取失敗件／尚缺件，不是另一個日更引擎。**本次已耗用唯一新attempt，禁止藉刪marker／改名稱再取**。再次呼叫只核既存完整及partial原bytes，GET0／檔案新增0。舊producer已封存且原intake.cached讀取仍為0GET，不能把新的reader或時鐘套回舊捕捉重新升格。

新來源／診斷使用已存在DU2無損codec，讀回SHA一致；舊partial、舊plain原件不壓縮覆寫／不移動。小型Source IO view只讓**原market_increment.sources**讀到完全相同bytes，沒有第二套日期／市場／價格計算。真實GET當時producer原bytes見producer-used；最終相容性修正版本與實際GET producer分開，不冒稱後改的程式曾發出新請求。

## 本輪必要驗證

10唯一Python方法PASS：完整／截斷／chunk終止、歧義framing／encoding、body與硬時間上限、403無重試、既有custom opener、原正式intake接線、DU2原bytes及原來源閘／重送。合成完整六件只證工程，不冒市場新日。初批runner誤收舊12個類別，都在setUp因舊目錄存在而停止、方法內容未執行／舊檔未寫；失敗log完整保留，修正後只跑新方法。中間8／9／10不累加，不重跑舊全套。

真實新attempt重送0GET、0新增；原intake讀回舊attempt也0GET。390／1280兩個實際owner瀏覽器流程通過：新拒用收據與原因、原11/3日期／1986清單、原上櫃精確價量及刷新保持；401仍拒絕。沒有重做前輪26流程、沒有Cloud／owner重啟、沒有新日核心或Android本人實測。

實測源請求8.660秒；報告的process ru_maxrss337664KiB含啟動高水位，不把它全歸為網路讀取。真實驗收時FS淨增約1.91MiB、free560,877,568 bytes，仍大於536,870,912最低保留；最終餘量見Git讀回收據。原FM3 metadata90377與原head保持，未重做19GiB全SHA。獨立備份／重啟持久性仍UNKNOWN，原警告、來源0.10與parents、策略／false/null全部不變。

## 唯一阻礙及下一步

**原官方上櫃HTTP傳輸仍提前EOF**；此次授權已耗用，因此停止新日接件與分析。來源宣告Accept-Ranges:bytes且有相同強ETag；最短下一步是總監另行核准、界定一次**同URL／同ETag的有界Range續傳**，完整Content-Range／總長／SHA與原六件日期閘仍須通過。這只是後續候選操作，本輪沒有送Range、加供應商、啟新服務或修改條款。

Git僅程式、合成測試與不可還原摘要／收據，全部真實行情／partial／完整Journal／憑證Git外。Oracle、網路部署、排程、交易均未觸動。保存固定SHA逐檔原bytes讀回後結案，不以工程PASS稱新日更新成功。
