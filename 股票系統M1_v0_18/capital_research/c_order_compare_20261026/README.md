# C原單保存結果：直接閱讀

本輪只用已保存原件，沒有重跑回放或計算帳務。兩組可並列；另外四組保留拒比原因。

| 入口 | 結果與用途 |
| --- | --- |
| [合格重評／資格未知仍等待](actual/reviewed-versus-unknown-wait/readable.txt) | 同起點、市場、截止：原單B20成交對0成交／活單20；僅資格診斷控制，不選勝者 |
| [未來撤銷尚不可知](actual/unknown-future-revocation-prefix/readable.txt) | 同當期前綴可以並列；完整來源ID不同仍原樣保留 |
| [容量20與7](actual/capacity-mismatch/readable.txt) | 拒比，容量不同不能當策略差異 |
| [OPEN與漲停](actual/market-state-mismatch/readable.txt) | 拒比，外生交易狀態不同 |
| [1/9與1/12截止](actual/cutoff-mismatch/readable.txt) | 拒比，不補行情或截短原件 |
| [C帳1430與舊E帳1330](actual/opening-account-mismatch/readable.txt) | 拒比，期初B5與B0、資本及token不同；不是同一C單控制 |

每個文字檔相鄰的`actual.json`保留完整原摘要、共同條件／差異路徑及來源ID。另見[報告](REPORT.md)、[事前契約](CONTRACT.md)、[六案索引](actual/summary.json)、[4方法log](tests.log)、[自審](self-review.json)。既有原件未複製或改寫，引用路徑與SHA見各`cases/*/input.json`及[intake](intake.json)。

在原工作區直接唯讀並列：

```bash
cd /workspace/Twstockai/股票系統M1_v0_18
python3 -B -m capital_research.lifecycle_compare_read \
  '原C單重評合格=capital_research/c_order_review_20261026/after-checkpoint-fix/valid-C-same-order/actual.json' \
  '資格未知仍待重評=capital_research/c_order_review_20261026/after-checkpoint-fix/unknown-current-eligibility/actual.json'
```

拒比範例只需把第二個label與路徑換成：

```text
另一容量7=capital_research/c_order_review_20261026/after-checkpoint-fix/partial-C-same-order/actual.json
```

同條件成功exit 0，拒比exit 2；加`--format json`可看精確欄位。CLI只stdout，不寫檔、不修復、不重算。`build.py`是本輪保存READ證據用的外部寫入器，不是回放／數值producer；一般讀取使用上方CLI即可。

這裡的等待欄是「當期資格UNKNOWN，已有一次遭拒重評」，不是完全未重評。兩欄原資本、現金權利80、A10股份權利與一般reserve100共用同一期初；期末差異只投影原件。表內嚴格可用額不是可追加金額。全部合成，正式資格仍false／主壓力null，不能推論市場績效。
