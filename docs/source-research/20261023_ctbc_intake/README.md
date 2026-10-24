# CTBC研究接件狀態與0.10轉圖警告勘誤

本輪只完成遠端／既有證據核對、接件盤點與文件勘誤；未取得新研究包或CTBC表，不新增0.11，不改產品程式、catalog、來源原件、策略、資料庫、行情、歷史或舊成品。

從遠端907bc2984e87408c646dc76e132cfd4c84b2fdb4接續，已核包含固定0.10工程f423447c9396bfdd7c524f4c5f63173be1ebb47d；開始時遠端沒有後續。main仍9c5b168c09ba80010c74f03b9c537e8b7474256a。根最新節與0.10 WORK_HANDOFF全文、README／CONTRACT／REPORT及其全部文字／JSON／測試紀錄已實讀，庫內證據讀取清單見read-inventory.json。

## 新研究包未取得

- `/tmp/codex-remote-attachments`不存在。
- `/workspace/shared/downloads`及`/workspace/library-files`實際只有舊v0.17交付，沒有本輪研究包。
- 遠端907bc29的完整追蹤路徑，以及庫內／既有下載目錄70個ZIP中央目錄均未找到WORK_RESEARCH_HANDOFF.md或CTBC檔名。ZIP只查成員名稱，未冒稱新封包CRC／manifest／內容已核。
- 本輪使用者未提供新包檔名、GitHub路徑、可下載網址或原件URL／bytes；因此新WORK_RESEARCH_HANDOFF全文及CTBC原件／meta都未取得、未讀，未做來源HTTP請求，也沒有聲稱網路拒絕。
- 已請求研究包GitHub完整路徑或下載網址，不要求手機搬運原件。新CTBC表工程實益待實際原件及完整指令核定；現階段不建新產品版本。

目前只沿用使用者已明示界線：CTBC表限公司層級交叉佐證，年度、1101／1101B、日期角色及精度分開；不重計事件、不證個人到款或完整覆蓋。不因這段指令就認定表內任何數值／日期已核。

## 0.10警告文字勘誤

上輪REPORT與三根交接前綴寫「全部stderr空／未出現Fontconfig警告」，與固定工程實際紀錄不符。已從固定f423447的GitHub raw實讀pdf-extraction-verification.json，HTTP200／5540bytes，對Git blob完整bytes相同，SHA cd6a2fd72e8e08a3d58f3393464baf6a5c429a8ed37ddcc858eb147dec86fe4e。

實際五頁轉圖皆return0；四頁議事錄stderr空，表決一頁含 `Fontconfig error: No writable cache directories`，須保留字型快取診斷。抽字stderr皆空。這項勘誤不證轉圖失敗、不撤銷已保存的視讀，也沒有重抽／重畫／改系統設定；不抹除舊公開說明書xref歷史警告。逐頁結果與讀回URL見warning-erratum-evidence.json。原0.10 REPORT、來源JSON、PNG、catalog、SHA／ZIP全部留史不改；往後解讀舊報告時併讀本勘誤。

## 本輪實際執行與未執行

文件寫入前重新bootstrap成功：0補缺／7差異保留（bootstrap.log）。只有Git唯讀、文字／JSON讀取、70個ZIP成員名稱盤點、兩份既有收據與一份固定警告JSON的原bytes讀回，以及文件保留／指紋檢查。沒有新產品行為，因此沒有新增產品測試、回歸、producer、每日帳或六方案；上輪53、70拒算／2不足／8未支援／合格0均屬歷史紀錄，未冒本輪重跑。

六項狀態：新研究包及CTBC原件未取得；WORK_RESEARCH_HANDOFF／表內容未讀；CTBC產品接入未實作；新產品producer／績效未執行；新產品／回歸／Android未測；新CTBC來源／產品未GitHub讀回。這些與本輪文件核對／勘誤的固定逐檔GitHub讀回分開，見 [delivery](../../../deliveries/m1-ctbc-intake-20261023/README.md)。

全部舊來源限制、原版本／parent null、Raw null、UNKNOWN、策略、庫與main保持。execution_qualified=false；imputed_close／valuation=null；historical_signal_eligible=false；primary_pressure_id=null；policy_authorized=false。缺資料未知／拒算，不補零、行情或估值，私人原件不公開。無新UI不重開Android；不重試／繞過既錄受拒入口，不部署、付費、交易、訊息或子代理。

完整下一輪Work唯讀指令：[WORK_HANDOFF.md](WORK_HANDOFF.md)。需要先交回可存取研究包位置，後續工程仍回此原唯一Codex。
