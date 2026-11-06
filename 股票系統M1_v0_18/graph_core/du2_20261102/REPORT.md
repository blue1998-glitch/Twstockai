# M-DU2局部儲存表示法契約與實測

## 範圍與原件

原環境running、同一環境ID，原工作區/workspace/Twstockai；起始本地與遠端均f782552，tracked/index空，無活躍更新者。依原AGENTS bootstrap --hydrate-missing成功、恢復0檔，7個歷史差異保留。沒有新任務、代理、分支、資料庫或原始資料遷移。

只讀盤點FM3根19,596個檔案路徑。邏輯31,157,700,168 bytes含重複路徑及硬連結；獨立inode檔案配置20,508,598,272 bytes（19.10 GiB），沒有把du多路徑重算當物理使用量。結果9,338,386,192 logical bytes，預覽20,962,473,240 logical／10,285,154,304 allocated bytes是主要占用；原始來源382,942,346 logical bytes不是主要瓶頸。各類見storage-audit.json。

不同inode但同名series的4,178檔、10,156,485,246 bytes實際串流SHA核對全符；額外相同內容6,679,143,079 bytes。這只是重複內容核對，不是重跑辨識／原API或公司行動驗收。舊檔未合併、刪除或移動，reclaimed=0。完整盤點及路徑級指紋留私人目錄；公開僅總量。

## 附加式格式與向後相容界線

保留rotation-record/0.1完整JSON契約和logical key。Journal原save預設仍寫完整.json；新協調器official-market-increment/0.2明示compact寫附加表示法。現有完整.json讀寫不變。新reader能讀舊檔；任意未升級舊程式直接Path.read_bytes不能讀新的logical-only路徑，須先以新reader還原完整檔。沒有宣稱舊二進位自動理解sidecar。

附加格式：

1. `.du2-root.json`綁私人儲存root；logical檔旁`.du2`描述原bytes長度、SHA及格式。
2. exact-byte-chunks/0.1以內容界定片段，引用舊原件精確offset／長度／SHA或du2-blobs下不可變gzip片段。新資料以SHA定址，不覆蓋舊片段；既存gzip若壓縮header不同，先核原內容後重用，不改它的bytes。
3. exact-interned-bytes/0.1只用原chart serializer（移至stdlib獨立模組）的節點重用，固定錨點在du2-intern-anchors或既存原series。每日新wire保留同一固定基底並附新節點，不承接昨天累積的無效節點；四代合成測試確認固定錨點。Journal與chart各有明示序列化格式。
4. reader還原value後依原完整JSON格式序列化，再核原bytes SHA／長度；HTTP回應及下載看到的JSON／HTML仍與未壓縮對照完全相同。不能只拿解壓成功代替精確核對。讀取不補算指標、辨識、修復或寫入。
5. 原pack預設與固定f782552版本逐值相同；只有儲存wire使用可選base。JS、資料schema、原核心、參數、價格／量、時間及資格不改。無浮點降精度或補零。

格式有長度上限、來源root／相對路徑／symlink／片段與完整bytes指紋檢查；拒跨root引用、路徑穿越及巢狀recipe。根標記及匯出拒Git目錄（含ancestor symlink）。原JSON適用既有讀法，新sidecar需Journal／codec IO界面；市場主流程與MOB1讀取接點已接通。

可逆：materialize將logical artifact輸出至另一Git外路徑，輸出bytes與原未壓縮完整格式完全相同；不覆寫唯一原檔，不自動將全庫展開。Rollback到舊reader前應在有足夠容量的私有位置還原需要的完整檔並驗SHA，不可刪掉共用依存後才嘗試還原。

## 原協調器、容量與錯誤

沿原Journal／daily.lock／core0.2／分段指標／market_preview。明示接受固定DU1 0.1 producer SHA與同engine的儲存接續，未知producer拒絕；不放寬資料來源或跨基底條件。舊完整history/result及舊head保留。

舊17.8 GiB係2倍結果＋history的保守metadata估算。新compact前置只預留最大單股邏輯大小兩倍＋64 MiB工作空間；每片／recipe實寫仍檢查64 MiB餘裕，未完成全批不發布新head。這不是全批容量保證，若累積資料超過磁碟仍會在checkpoint停止，不能為成功而自動刪資料。

片段先不可變寫入／fsync／讀回，再提交描述檔，再保存checkpoint；中斷保留有效片段，重跑只處理未完成股票。缺片、竄改、partial file或不支援型別拒用，不自動覆寫修復。未被引用的中斷片段也不自動GC，必須納入容量風險。修訂另版；相同來源重送0核心／0新成品。原驗證／預覽失敗保舊head語義維持；發布後目錄fsync故障仍明示COMMITTED_DURABILITY_UNKNOWN，不假稱回滾。

MOB1驗證及白名單保留，logical GET／HEAD經codec讀取，缺片或內容變動回409，不退回其他股票／舊圖。只允許同時一個完整HTTP重組控制每程序記憶體；沒有公開listener、CORS放寬或外部部署。讀取程序不匯入core／MACD，fresh-process測試通過。

## 實測設計與結果

公開benchmark.py可重現：先唯讀選上市與上櫃各三個既存結果大小分位（0.2／0.5／0.9），另取最少根數的歷史不足例，共7前綴。不是隨機樣本。私人對照根只用原檔唯讀hardlink alias；獨立目錄明示SYNTHETIC新日11/3、11/4，資料價量由保存末筆複製構造，時鐘11/6僅工程注入。沒有取得這兩個真實交易日行情，不能作市場績效、策略或新資料成功樣本。

同一capture／seed／核心，分別以完整plain與compact編碼，在各自新Python程序連續跑兩輪；庫內原件不搬移。stat.st_blocks計新增獨立inode檔案配置量，排除既存aliases，未含目錄／inode table額外開銷。RSS是該程序截至當輪的最高值，並非第二輪獨立reset峰值。

| 模式／輪 | 新增檔案配置bytes | wall秒 | peak RSS KiB |
|---|---:|---:|---:|
| plain 1 | 56,229,888 | 17.523 | 122,724 |
| plain 2 | 56,233,984 | 17.188 | 125,404 |
| compact 1 | 5,226,496 | 53.755 | 289,936 |
| compact 2 | 1,900,544 | 51.593 | 289,936 |

第一輪包含建立共用基底；第二輪已有基底。兩輪42組result／history／series完整原bytes逐一相同，全部source binding、核心ID、Raw／volume精度、缺口、日期與false／null資格皆在比較中。每模式14次合成續接核心呼叫，最終對照合計28；先前單純分片壓縮prototype另有28次，均私人留史，不重複計最終方法或市場樣本。prototype約82%～86%節省後，才加入固定節點基底，沒有改數值oracle迎合壓縮。

27唯一Python＝25新增＋2必要Host／Origin／唯讀路徑安全回歸。涵蓋原bytes、Unicode、舊格式、物化還原、固定基底、不重送寫入、篡改／缺片、同源零重算、修訂、IO中斷續跑、容量失敗／預覽失敗保舊head、固定0.1 producer接續、原圖與新圖讀取、限一個HTTP重組、Git外保存。沒有重跑M-DU1舊27、FM3補建、全套MOB1或策略測試。中間PASS不加總。

30 Chromium檢查／18完整下載：桌面1280×900、手機390×844及844×390，讀原10/30兩股＋兩個合成新批。3個selector檢查、9個原真實保存圖檢查／6下載、18個合成批次檢查／12下載；全核core、bars、量、MA、MACD與保存內容相同，按需一股、截止、共軸、縮放／移圖／觸控及無橫溢，JS錯誤／外部請求0。不冒Android實機或真實新日。

原19,596路徑尺寸／mtime／inode無改變，原HTML SHA相同；21個原檔因私人benchmark唯讀alias增加nlink，未改原bytes。原core.py、market_daily.py、market_finmind.py、MACD及MA源碼與f782552一致。詳細路徑盤點、完整數值、圖、PNG、下載、樣本及所有原件均Git外。

## 容量外推與限制

capacity-forecast.json將原全體結果logical bytes／樣本原結果bytes作比例外推，另明示517無既存結果者每檔64 KiB、來源整批64 MiB／日及run/checkpoint 16 MiB／日情境。這些額外預算不是實際新日測量，也不保證涵蓋所有新增／修訂。用11/2舊1986參照，不冒其他日已核母體。

按此模型，未改善約11.89 GiB、改善第一次約1.205 GiB、後續約0.508 GiB／日。不是完整市場實際寫入量，不宣稱舊17.8 GiB估算已被全量驗證。非隨機7例、兩輪、合成新日及新事件密度可能產生外推偏差；真實修訂／失敗片段／檔案系統開銷／獨立備份另計。

示例磁碟50／100／200 GiB，各留20%空間，保留原19.10 GiB、不含獨立備份，扣初次建基底後約38／117／275個後續交易日；若日增量兩倍則約19／58／137。**不是已核Oracle免費quota或永久保存承諾**。沒有啟自動修剪，保留期／加容量需依真實新日與核定quota決定。

## 真實來源、停止與交接

本輪官方／FinMind請求0。台北11/2時，10/30之後未有早於台北當日的下一weekday可被原gate接受；未為取得成功重試DU1不完整TPEx入口。只重新套用已保存DU1 capture，仍BLOCKED／exit2，1986未套用診斷、舊head保持。真實新日0、真實新增圖0；合成結果不搬入正式FM3 root或實際使用者入口。

Oracle帳戶未處理、未部署／VPN／外部傳輸／付款／排程，使用者不需開終端或搬檔。備份／Oracle恢復必須包含整個原private root、legacy span原檔、隱藏root marker、全部sidecars／wire、du2-blobs、du2-intern-anchors、Journal／capture／head及預覽，不能只複製最新HTML。獨立私人持久儲存與隔離還原未核；不重啟原Cloud驗此項。

全部正式false、primary_pressure_id=null、imputed_close／valuation=null、來源0.10／parents、公司行動／歷史可得／Raw／五年Adjusted／主檔／SQLite未知保持，不增來源0.11或catalog，不跑帳務／六方案／績效。未覆蓋：真實新日完整1986批、完整年度新增、尾端最大股RSS、Oracle／Android實機／重啟恢復、所有硬體故障與發布後fsync注入、GC／無效片段清理。格式在本輪局部範圍已驗完成，沒有重大架構或付費授權需求；未解決的是實際quota、持久備份與真實新日校正。

本里程碑正常保存／固定SHA逐檔讀回後停止；等使用者明示Oracle帳戶完成，再由總監決定下一部署里程碑，不自啟研究或策略工程。
