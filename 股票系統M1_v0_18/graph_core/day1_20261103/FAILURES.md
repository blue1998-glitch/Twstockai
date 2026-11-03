# 本輪失敗、修正與未測

1. 首次真實處理程序退出狀態為 SIGKILL 9。當時 cgroup oom_kill=0，不能推定 OOM、平台故障或誰發出訊號。沒有最終初次 wall／RSS 收據。1986 終態及 264 完整圖保存，無新 head。曾把含 wire 的 529 個 sidecar 誤稱完整圖，已更正為 264，不沿用錯計。
2. 核同 Cloud／原件／工程鎖及已死 PID，hash 新檔／依存並綁合法 append 清單，再單一恢復原保存批次。原 73279 路徑 metadata 不變；恢復過程禁止核心呼叫。正常發布新 head，實際同源重送零重算／零新增。原 SIGKILL 原因仍未知；這是同檔案系統程序恢復，不是跨環境／重啟或備份還原。
3. 原新增空間診斷包含所有目錄區塊。真實資料根當時目錄共 12599296 bytes，不能全部當新增檔案。最初 4 合成控制 PASS，因 temporary 目錄回報零 blocks，未覆蓋非零目錄；後續保持同一 oracle「無新檔＝0」，明示兩既存目錄各 8 blocks，實跑 1 FAIL（8192≠0）／4 方法。最小修正只在新 DAY1 量測 helper 跳過目錄／symlink、按新 regular-file inode 去重，最終 4 PASS。另以真實新檔與檔案系統淨使用量分開量測。舊 private receipt、執行前 source 及失敗 log 全保留，沒有更動行情／核心／指標或重跑全市場。
4. 收尾摘要程式首次有重複 status keyword，另一次保護清單誤列 MA 路徑為根下 moving_averages.py；實際在 src/moving_averages.py。兩次在寫出公開摘要前失敗，修正摘要建構與檔案定位後完成。未重抓來源、重跑核心或重建圖。
5. 沿用的主瀏覽腳本某段標籤曾含「缺值日查詢」，但 cfg.query_date=null，所以該條件分支未執行。實際做的是 gap／basis-reset equality；文案已釐清，原 private log 留史，沒有冒稱測過缺值日。當日 11/02 查詢及近期可見性另以 390 寬 1 組實際通過；移圖／查詢不改分析日。

私人證據在 day1_20261103 Git 外目錄：兩次啟動及 stdout／stderr、progress-samples、interrupted／published inventory、execution-source-before-metadata-correction、初版／非零 fixture before／final log、browser-first、canonical resource 收據。公開只保存上述不可還原摘要、程式及合成控制。

未取得／未讀：沒有另取受拒來源、個人權利／淨分配原件；既有來源缺口未解除。未實作／未執行：Oracle、外部移轉、常駐服務、每日排程、交易、獨立備份。未測：真實 Android、低記憶體／慢網手機、重啟／跨環境恢復、跨來源連續公司行動資格、分類／收益品質。不得用本輪工程或同機恢復通過取代。
