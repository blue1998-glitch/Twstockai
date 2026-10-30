# M2-3｜FinMind Free 接既有圖形研究核心

已完成有限研究接線。**這是新來源輸入能力，不是圖形算法、買點或策略驗收。**

- [公開驗收摘要](real-validation-summary.json)：實際2884來源檢查與兩個分析日，只有不含行情的狀態／筆數／布林核對。
- [報告與限制](REPORT.md)、[事前契約](CONTRACT.md)、[合成輸入](input.json)、[預期](expected.json)、[合成actual](synthetic-actual.json)。
- 純函式：`graph_core.finmind_adapter.analyze_response(response, request)`；**完整回傳可還原行情，禁止進Git**。
- 明示本地執行：`python -m graph_core.finmind_run`。直接呼叫不需網頁、資料庫、UI或付費套件。

## 操作入口

在 `/workspace/Twstockai/股票系統M1_v0_18` 執行。已保存資料可直接重用，不須再查API：

```bash
PYTHONDONTWRITEBYTECODE=1 python -m graph_core.finmind_run \
  --response /workspace/twstockai-local-data/m2-3-finmind-20261030/response.json \
  --acquisition /workspace/twstockai-local-data/m2-3-finmind-20261030/acquisition.json \
  --output-dir /workspace/twstockai-local-data/m2-3-review-fresh
```

output-dir 必須不存在且在任何Git工作樹外。若已存在，原件保持且拒絕；請使用新名稱，不刪舊成果。stdout只輸出非行情白名單摘要。完整payload／結果／前綴控制只在外部本地目錄。這不是新的READ／Journal框架；沒有自動更新、恢復或選結果。

只有需要明示重新取得本範圍時，省略 `--response` 與 `--acquisition` 即只請求一次官方API：固定2884、2026-03-01～07-22、TaiwanStockPrice。無token、無註冊／付費、無全市場抓取；HTTP／API拒絕不重試。受限本地資料的保存不等於永久備份，工作區生命週期仍由平台決定，GitHub不保存它們。

## 實讀與驗證界線

實讀官方[Technical文件](https://finmind.github.io/tutor/TaiwanMarket/Technical/#taiwanstockprice)，依既存 `source_audit.parse_twse_month` 驗證TWSE欄位與原件SHA，再轉入原 `graph_core.core.analyze`。未改既有門檻、主壓力或算法。

Work M2-2兩份Library檔案未取得／未讀；依使用者明示範圍與已核摘要操作，沒有HTTP試探Library或要求搬檔。Free個人非商業限制沿用使用者已核條件，不宣稱獨立法律授權審查或已取得散布權。

8069只讀庫內07-21／22兩列官方整數張數以核顯示精度；沒有取得Library內FinMind8069原件，故本輪沒有重驗其FinMind價格。精確股數UNKNOWN，拒絕精確量認證；沒有將整數張數乘1000冒精確股數。

## 可重現合成驗證

`test_finmind.py`為15個新方法；另選原core三個相關保護方法。18個唯一方法最終皆通過，詳REPORT。原整套suite／資金producer／市場績效／UI／Android均未執行；已結清舊證據不累加。

`refusal-inputs.json`及其指紋是27份明示合成反例，不是真實行情。`verify.py`只物化合成actual，不增加測試方法數；使用新clone時可自行選讀既有結果，舊actual不覆寫。

驗收達成後停止；沒有全市場母體、歷史可得時間、Adjusted基底認證、跨公司行動連續結構認證、正式圖形／主壓力認可、買賣規則或績效。下一里程碑需外部另行指定，不自動擴張。
