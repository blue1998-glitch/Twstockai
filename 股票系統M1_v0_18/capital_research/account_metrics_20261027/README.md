# 全帳戶合成評估：現在能回答什麼

可以看一份**已完成且資料完整的合成回放**：原資本長了多少、途中離最高帳戶淨值跌多深、何時恢復，或到最後仍未恢復。不是選股、建單、清倉模擬或市場績效驗收。

原帳每天的應計淨值已包含保存的成交費用、應收應付及已知權利；評估器直接使用，不重建帳務。期末假想退出成本另列，不保證當天能清倉，也不把它每天再扣一次。期間成長與期末退出成本後成長分開，不年化或排名。

## 已保存、可直接看的證據

- [完整原帳評估](final/saved/complete-partial-chain/readable.txt)：原資本2230、期末應計淨值2225.640；已含原帳成交費稅4，再按原帳假想退出成本9.110得2216.530，沒有重複扣費。原一般reserve100、權利、latest與全部token保持。
- [手算恢復曲線](arithmetic/recovered/input.json)及[結果](final/arithmetic/recovered/result.json)：1000→1100→880→990→1100，期間成長10%、最大回撤20%、峰日至恢復3個日曆日。
- [未恢復手算曲線](final/arithmetic/censored/result.json)：恢復日null、持續日僅觀察截尾，不冒稱已恢復。
- [缺價拒算](final/saved/missing-held-mark/result.json)、[原價錯配拒算](final/saved/mismatched-mark/result.json)、[尚未可得拒算](final/saved/future-close/result.json)、[中途停止拒算](final/saved/stopped-result/result.json)。
- [契約](CONTRACT.md)、[本輪結果與限制](REPORT.md)、[唯一方法首次執行](tests-first.log)及[自審補強後6個相依方法](tests-final-related.log)。8唯一方法、14次方法執行；不累加歷史PASS或把案例數當市場樣本。

## 呼叫入口

在`股票系統M1_v0_18/`：

```bash
python3 -B -m capital_research.account_metrics_read \
  --source capital_research/quantity_replay_20261026/cases/partial-then-independent/actual.json \
  --evaluation-at 2026-01-12T16:00:00+08:00
```

加`--format json`保留完整數值／來源。這是**明示讀入原件並計算新評估**的入口，不是舊保存結果READ：不重新生成、執行交易或重播帳務；原有READ入口完全不變。退出0表示合成評估完成，2表示拒算。只輸出stdout，不找最新來源或寫入原件。純數值API為`account_metrics.evaluate_saved(request)`，IO在外層分開。

第一版限完整quantity-replay/0.1與全checkpoint，其他結果型別、停止結果或只有意圖均拒絕；不因已有數字就補通權利。外部流入流出、年化／風險調整報酬、現金拖累歸因、大贏家歸因、R1/R2勝負與樣本外尚未完成。真實1101帳戶證據UNKNOWN、70／2／其中8／合格真實總淨0、正式false／主壓力null保持。使用者目前無需操作。

`final/`與`cli-final/`／`time-final/`綁最終source；`actual/`、`after-final/`及`diagnostics/`保留先前階段，不能把舊指紋當目前source。原始input／expected未改；資本案例被既有較早防線擋下的差異已獨立記錄，不改oracle迎合結果。
