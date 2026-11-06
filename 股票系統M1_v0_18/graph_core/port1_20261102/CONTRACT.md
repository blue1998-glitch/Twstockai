# M-PORT1 工具契約 private-portability/0.1

這是原 Journal／DU2 codec 的本機附加檢查與拷貝工具，不是新儲存系統、資料庫、引擎或來源版本。所有讀寫資料均限 Git 外具體私人根；不接受廣泛系統根、Git 樹、symlink、外部依存或路徑穿越。不修補來源、不刪檔、不覆寫正式資料。

## 完整集合與指紋

逐實體路徑保存 bytes、SHA256、mtime、硬連結分組及觀察資訊。相同 inode 只讀一次；邏輯檔案總量與不同 inode 的實際占用分開。詳細清單可能還原私人資料結構，只可私存，不進 Git。單一清單 SHA 與統計可公開。清單摘要防止意外竄改，不是數位簽章或來源真偽認證。

原 Journal envelopes／ID、FM3 producer 0.1、core 0.2、對象／截止／receipt、原件 SHA、保存核心 result_id、history／預覽 K／完整結果／MA／MACD 逐值配對。保留原拒用股票、false／null；不重新計算核心／指標或評估策略資格。原件可讀不證日曆、公司行動或歷史時點完整。

DU2 以原 codec 讀回精確 bytes，檢查 `.du2-root.json`、span、gzip blobs、intern wire 及後續接續所需 anchor。全部歷史 Journal 的 run／checkpoint／parent／source／history／result 引用及舊預覽也要閉合；不僅 latest HTML。已有明確拒絕的 capture 缺原件保留拒絕，不造成功來源。未知 producer 的商業規則不自動認證。

檢查與恢復綁相同 store.py、artifact_codec.py、interned_json.py 的 SHA／版本；未來須攜帶本工程固定 Git 提交及相容 Python。來源正被更新或有原 writer 鎖則拒絕，不清鎖。daily.lock 只開既存檔、唯讀共享鎖；不在來源新增鎖。來源應在整段複製期間保持停止寫入。非合作寫入者仍可能競態，輸出僅在全量來源／目的讀回相符後標 ready。

## 隔離恢復

目的目錄必須全新、與來源不重疊、位於已存在私人父目錄。先核容量，再全來源 SHA，再獨立複製；目的內部保留 hardlink 分組，不跨回來源 hardlink。新根 0700、檔案 0600，保留內容與 mtime；不是所有權／原 ACL 完整複製。檔案及目錄 fsync；不保證所有遠端檔案系統／斷電語義。

部分失敗為 INCOMPLETE_NOT_READY，保留副本與收據；只有 manifest、來源、目的綁定相符才能續跑，不覆寫已存在的損壞檔。容量估算包括不同硬連結組、磁碟區塊及保守 reserve，非免費雲端 quota 認證。

恢復後逐檔 SHA、DU2、Journal／FM3 語義及硬連結分組雙向核對，不能意外合併不同組。`verify` 不需讀舊來源。舊 JSON 的絕對指標不改；另存私人 access overlay 供既有讀者使用。未成功不得切換正式 head。`VERIFIED_LOCAL_COPY` 只代表本地一致副本，不代表跨機／持久／獨立備份。

## 安全及範圍

manifest 及收據必須隨完整資料另行保護；只備 latest 頁、最新一個分片或公開摘要不足。檔名憑證警示不是全面敏感資料掃描。真正移轉之前仍需審查私密內容、主機 ACL、加密、備份、磁碟及來源使用範圍。工具沒有外部傳輸、帳戶建立、登入、排程或部署功能。

合成集合與真行情分開；不造真行情、不呼叫辨識引擎或來源 API。來源0.10及全部 parents、正式 false、primary_pressure_id=null、imputed_close／valuation=null、Raw／UNKNOWN 不改。不執行日淨帳、六方案、Android、Oracle 或來源重抓。真實完整復原／新主機切換留待授權與持久儲存就緒。
