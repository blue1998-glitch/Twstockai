# 獨立期初權利證據缺口檢查

先讀 CONTRACT.md 與 REPORT.md。純核心為 `capital_research.opening_evidence.check(data)`，只接明示合成輸入、回傳診斷，不讀寫檔案或呼叫帳務。格式錯誤／未支援真實入口拋 ValueError；缺證據、未知、錯身分、晚可得等列入診斷缺口。

讀保存結果：直接用檔案讀取 cases/*/actual.json、summary.json、tests-final.log，無需重新執行核心或測試。不累加任何歷史PASS；本輪數字以 REPORT 與 execution.json 的21唯一新方法、22個合成案例為準。

若需只讀核對指紋，在股票系統M1_v0_18執行：

```sh
python3 -B -m capital_research.opening_evidence_20261026.verify
```

verify只讀檔／Git差異／JSON／log，不呼叫核心、測試、producer或寫檔。它核對的是未提交本輪基線；日後保存提交後index新增屬狀態改變，不能把這份原基線審查程式當通用已提交驗收工具。

build.py本輪已執行一次；已有actual時明確拒絕。後續新版本必須另存新目錄並先保存input／expected／版本，不能刪actual再重建。禁止把真實資料改標synthetic繞過來源門檻。沒有UI、來源下載、私人資料或交易入口。
