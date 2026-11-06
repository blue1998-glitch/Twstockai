# M-PORT1｜私人資料檢查與隔離恢復

本輪在原 Cloud 實際讀到 FM3，核對 **1,986 終態、1,986 原件指紋及 1,469 組結果／歷史／研究圖**。新工具完成 **16 項定向測試及一次合成 CLI 隔離恢復**。沒有建立真實獨立備份、搬移原件、重算股票或部署服務。

[驗收與限制](REPORT.md) · [工具契約](CONTRACT.md) · [真實來源唯讀核對](real-source-verification.json) · [合成恢復](synthetic-restore.json) · [測試及失敗](verification.json) · [容量](capacity-and-boundaries.json) · [原件保存](preservation.json) · [既有程式不變](protected-source-verification.json) · [GitHub 固定提交讀回](GITHUB_READBACK.md)

| 驗收 | 本輪結果 |
|---|---|
| A 原 FM3 是否可讀 | 是；本原檔案系統可讀。其他環境先前缺根紀錄完整留存。 |
| B 1,986 終態及 1,469 圖完整性 | 本輪重新檢查保存物件、SHA、對象、截止、版本與完整依存；不等於重新驗證圖形品質或 Android UI。 |
| C 檢查／恢復工具 | 已實作；16 個唯一新測試方法通過，沒有累計歷史或中間批。 |
| D 合成隔離恢復 | 成功；23 個實體檔、9 個 DU2 邏輯成品，原 bytes／硬連結分組一致，驗證不需舊來源。 |
| E 真實獨立備份／新環境復原 | 未建立、未驗證；其他不可見備份是否存在未知。重啟／跨主機未測。 |
| F 未來私人主機 | 需授權的持久私人磁碟、完整備份、足夠容量及相容程式；Oracle 帳戶與部署繼續暫停。 |

## 未來 Codex 單次入口

下列為操作員入口，不要求使用者在手機執行。從「股票系統M1_v0_18」執行。所有清單、原件、恢復副本及收據須在 Git 工作樹外；工具不傳資料到外部。範例路徑僅代表未來已授權的本機私人掛載點，不會自動建立主機或掛載磁碟。

```bash
python3 -m rotation_research.private_portability inspect --root /private/fm3/runtime --manifest /private/port1/fm3-inventory-private.json
python3 -m rotation_research.private_portability restore --root /private/fm3/runtime --manifest /private/port1/fm3-inventory-private.json --destination /private/restored/fm3
python3 -m rotation_research.private_portability verify --root /private/restored/fm3 --manifest /private/port1/fm3-inventory-private.json
```

先建立受保護的 `/private/port1` 及 `/private/restored` 父目錄。manifest 每次用新檔名保存，不覆寫舊證據；來源變動須重新檢查。只對工具自有、中斷且仍相符的目的目錄使用 `restore --resume`。損壞的部分檔案保留並拒絕，不會偷偷重寫。缺原件直接拒絕，不能用 `--profile generic` 冒充 FM3 驗收。

原 JSON 中的絕對路徑保持原 bytes。目的目錄旁的 `.port1-receipt/access-overlay.json` 與 `relocated-batches.json` 提供新位置的讀取配方，可交既有 M-MOB1 `batch_index`；工具不啟動手機服務、不更換正式 head。正式切換之前另需安全入口及持久性驗收。

## 重現工程演練

```bash
python3 -m unittest graph_core.port1_20261102.test_portability -v
python3 -m graph_core.port1_20261102.rehearse --work /private/port1/new-synthetic-rehearsal
```

演練只重用庫內公開 COMP1 合成示範中已保存的 69 根 K 及核心／指標，零引擎呼叫、零供應者請求。每次使用新演練目錄，拒絕覆寫。實際本輪結果見 `tests.log`、`synthetic-restore.json`。這不是市場樣本、獨立持久備份或重啟測試。

真實來源仍有原限制；正式資格 false、主壓力 null、Raw／公司行動／歷史可得／SQLite UNKNOWN 不變。每日更新、Android 固定入口及 Oracle 未啟動。本里程碑交付後停止，待帳戶完成後由 Work 總監核定私人持久儲存與真實備份／復原，不自啟下一工程。
