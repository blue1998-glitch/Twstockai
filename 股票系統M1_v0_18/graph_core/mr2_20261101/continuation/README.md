# M-R2 原里程碑續作｜有限研究日簿0.1

**工程已完成本次有限範圍；真實研究接線為PARTIAL。** 2884兩日的原圖形事件，已連結同日兩市場的「總監讀回研究摘要」。不是官方原件重新驗證PASS，也不是正式交易日簿。

- [實際真實接線摘要](real-actual-final-summary.json)：2個日期成功連結，官方市場重新驗證PASS仍0。
- [事前研究契約與角色判斷](../CONTRACT_0_1.md)、[交付報告](REPORT.md)。
- [合成原輸入／預期](synthetic-input-expected.json)、[9案實際結果](synthetic-actual.json)、[最後來源一致性](final-equality.json)。
- 本輪測試：14唯一方法最終通過，12新增＋2必要F-01回歸；初批診斷留在tests-first.log，其餘分批log均不重複加數。

原`mr2_20261101/README.md`與其BLOCKED actual／log／manifest保留為前一階段歷史；本目錄是**原M-R2的補正交付**，不是另一個里程碑或平行引擎。

## 能做什麼

`graph_core.event_diary.build(request, as_of=...)`只讀供應的原graph input與保存0.2結果，檢查完整來源、前綴、基底、缺漏、原確認日及F-01；不呼叫辨識分析，不改原事件或參照。對上同日TWSE、TPEX摘要，原pivot ID保留；箱路徑本來沒有事件ID／confirmed_at時保持null，另記派生日簿key及原定位，不能冒充原事件ID。

每天的已知entry不被後一天改寫，後續觀察另列followup_updates及evaluated_at。已知失守即記原失守事件；未成熟不當成功，完整窗未失守只表示該明示研究窗未見原失守事件，沒有勝率／獲利含義。跨基底／缺資料拒判，仍保留中斷前已見失守。原始行情、完整圖形／日簿與市場數字都只留本地。

## 本地操作入口

在`/workspace/Twstockai/股票系統M1_v0_18`：

```bash
PYTHONDONTWRITEBYTECODE=1 python -m graph_core.event_diary_run \
  --request /workspace/twstockai-local-data/mr2-20261101/continuation/research-input.json \
  --journal-dir /workspace/twstockai-local-data/mr2-20261101/journal \
  --as-of 2026-07-22 --key mr2-diary-research-2884-20260722-v01
```

這是明示RUN，只重組保存結果，不抓來源／重算圖形；相同key與內容沿原Journal不重寫，異內容拒絕、不覆蓋。完整request／journal只能在Git外，stdout是白名單非行情摘要。

純READ直接用原`rotation_research.store.Journal(...).read(key)`，不經新RUN，也不新增READ資料庫／框架。7/21保存key為`mr2-diary-research-2884-20260721-v01`；原兩個`mr2-blocked-2884-...`紀錄原樣留史，沒有以新結果覆蓋。

## 仍不能證明什麼

市場數字和原報表SHA來自總監本輪提供，只保存`DIRECTOR_READBACK_RESEARCH_SUMMARY`與reported SHA；Codex沒有取得Library ZIP或四份市場官方原件，也沒有獨立完成那些SHA讀回。Codex本輪親自讀回的是原FinMind個股回應及其收據，與既有input逐值核對，和市場原件角色分開。

歷史公布時間／嚴格普通股母體／公司行動／市場摘要散布權UNKNOWN，全部正式資格false、primary_pressure_id=null。真實HIGH沒有已批准失守定義或觀察窗，本輪不補天數；7/22沒有後續完整K，所以IMMATURE，失守評估仍未知。2408沒有可核原件仍BLOCKED；本輪沒有擴抓或用合成冒充。

全市場成功／失敗率與真實淨績效始終null／拒算。沒有停買、減碼、持現金、恢復、換股、排名或參數挑選；未重抓81日或舊全套。下一階段唯一主要限制仍是市場原件及歷史可得時間的來源資格；本輪不自動延伸。**人工操作：不需要。**
