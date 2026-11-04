# M-CAP1｜資金行動比較器

成品是可下載離線操作的**純合成單檔HTML**，只重用原資金／帳務引擎。不是真實績效，也不選最佳行動。

[下載與Android步驟](../../../deliveries/m1-cap1-20261104/README.md) · [手機實際畫面](validation-final/portrait-reduce.png) · [完整比較結果](artifacts/comparison.json) · [契約](CONTRACT.md) · [實測報告](REPORT.md) · [固定SHA讀回](GITHUB_READBACK.md)

可比較續抱、減碼B3、退出B7（仍持C）；全退出持現金缺全資產執行與權利證據，明確拒算。

程式分工：compare.py只驗證同基準及調原metrics；build.py以原evaluate／execute重現3支並沿Journal保存；package.py只讀保存結果封裝；render.py＋viewer三檔只做顯示。Journal原物件逾1MiB，另有[小型完整收據索引](artifacts/portable/manifest.json)，每份UTF-8小於512KiB，解析物件完全相同，不要求Work取大檔。

工程者依根AGENTS取得即時Cloud ID後，由同一gated --run入口、PYTHONPATH指既有v0_18執行：

```text
python3 -m capital_research.cap1_20261104.build
python3 -m capital_research.cap1_20261104.package
python3 -m capital_research.cap1_20261104.verify <新證據標籤>
python3 -m capital_research.cap1_20261104.browser_verify <新證據標籤>
```

build重現純合成帳務，不碰市場，使用新目錄immutable輸出；既有輸出不同就拒絕，不覆寫。package只重封裝，不呼叫帳務／指標。來源與原碼指紋在source-manifest及engine-preservation；初版成品／PNG與初版build原碼留存，最終交付以v01為準。驗證證據標籤須新名稱，不能覆蓋既有日志。本輪已驗，Work無須重跑。

能力只到合成帳戶比較基礎。正式市場判定、交易決策、配置風控、真實總淨報酬、方法近期適用性及自適應切換均未核准／未完成。只交Work用途差異檢視，下一指令見WORK_HANDOFF.md。
