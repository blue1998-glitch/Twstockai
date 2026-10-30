# 保存候選的明示研究選擇紀錄0.1

現在能從已保存的generation，明確記下「我選哪個候選、理由是什麼」。它不替使用者選比例，也不重算候選、帳務或行情。這些都是合成研究紀錄，不是交易建議或委託。

直接閱讀：

- [一般研究意圖：新增B1股](views/grid-intent.json)
- [全換：只能記為等待交割重評的條件意圖](views/conditional-intent.json)
- [舊觸發不合格：保留拒絕紀錄](views/rejected-old-trigger.json)
- [完整結果](after-final/summary.json)、[契約](CONTRACT.md)、[驗證與限制](REPORT.md)

每份選擇綁定完整來源指紋、原帳、截止、latest與全部歷史／當期reviewed tokens。相同候選ID在不同generation可能有不同資格，不能跨來源借用。來源generation的selected_id仍為null；選擇只存在新紀錄中。

## 使用入口

在`股票系統M1_v0_18`下，純API為`research_choice.choose_saved(request)`；外部保存API為`research_choice_workflow.select_and_save(store, id, request)`。

已保存的例子可直接唯讀：

```sh
python3 -B -m capital_research.research_choice_cli READ --store capital_research/research_choice_20261027/journal --id grid-intent
```

新增紀錄使用同一CLI的`SELECT --store <目錄> --id <明示ID> --input <完整輸入JSON>`。輸入契約見CONTRACT；必須有完整saved_result、相符source_binding、明示selection與recorded_at，不接受候選ID單獨下指令。研究輸入的引用／指紋組裝方式在fixtures.py；不是回放入口。

SELECT與READ分開。Journal的同ID相同內容可讀回；不同內容拒絕覆寫。選擇不合格也能保存REFUSED紀錄，CLI退出碼2；這不等於保存失敗。IO的UNKNOWN須另READ確認，不自動刪除、修復或重新選擇。

現存行情窗口止於1/12；記錄時間不代表新增歷史可知資料，也不提供後續成交證明。目前不需要人工操作，無須轉貼給Work才能完成一般工程自審。
