# M-CAP1 0.2｜全帳退出持現金補正

[下載新離線示範](../../../deliveries/m1-cap1-full-cash-20261104/README.md) · [手機全現金畫面](validation-initial/portrait-cash.png) · [已賣出尚未交割](validation-initial/portrait-cash-2026-01-07.png) · [完整結果](artifacts/comparison.json) · [契約](CONTRACT.md) · [實測](REPORT.md) · [GitHub讀回](GITHUB_READBACK.md)

新合成帳戶共同期初NAV1240、B7／C4均已交割，四方案＝續抱、減碼B3、退出B保留C、全退出B＋C。全退出在1/9明示交割完成後才是全現金，期末現金／NAV1235.760、持股與未交割款／權利均無。一般reserve100仍保留。不是原1180帳戶的C權利解除，原三方案／舊成品完整不動。

最小接線：前三支沿cash_action／cash_action_execution；basket只補多股意圖／範圍／來源／全量委託校驗，仍呼叫原core.resume_decision、execution.simulate、continuity.make_checkpoint。源READ復用_pair／_chain與原account_metrics共享統計；沒有第二套成本／帳務／績效引擎。audit只檢查保存日終的持股／權利／交割事實，不做估值。

主要證據：declaration-v03（最終合成宣告，執行前固定oracle）、original-refusal-summary、artifacts/comparison、artifacts/portable/manifest（每份≤512KiB的完整原Journal物件）、counter-inputs／artifacts/counters兩個實跑反例、tests-initial／tests-final-guards、validation-initial/browser-verification、preserved-source-manifest、preservation、resources。

初期兩次時點拒絕、包裝器讀取失敗專用欄位的KeyError與定向原件均保留。build-completed計數勿作本次呼叫，讀build-count-correction與build-verified。初始0次成功不能冒後來成功；只有最終四方案資料可做操作入口。

工程者在原Cloud依根AGENTS即時取ID、透過unified_workspace --run與既有v0_18 PYTHONPATH執行：

```text
python3 -m capital_research.cap1_cash_20261104.build <新的檢查紀錄標籤>
python3 -m capital_research.cap1_cash_20261104.package
python3 -m capital_research.cap1_cash_20261104.verify <新的測試標籤>
python3 -m capital_research.cap1_cash_20261104.browser_verify <新的驗證標籤>
```

所有輸出immutable，同內容可讀回，衝突拒覆寫。builder核既存Journal與共用來源後可0呼叫續讀；不自行重抓或修補缺失。這些是Codex重現入口，不要求Android使用者開終端／架站。手機只需ZIP中的HTML。

Android實機NOT_TESTED_NEW_BUILD；無新私人／公開網站入口。所有正式交易資格false、主壓力null、真實來源及淨額缺口保留。本輪結清只交Work用途檢視，完整指令在WORK_HANDOFF，不能自開策略適應或下一工程。
