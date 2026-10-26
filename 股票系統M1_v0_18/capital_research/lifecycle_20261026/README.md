# 原批次生命週期摘要

純API為`capital_research.lifecycle.summarize_saved(saved)`；檔案讀取另在`capital_research.lifecycle_read`，沒有RUN或修復路由。正常只讀指令請使用`-B`避免Python產生bytecode快取：

```bash
cd /workspace/Twstockai/股票系統M1_v0_18
python3 -B -m capital_research.lifecycle_read capital_research/conditional_quantity_review_20261026/after-final/partial-original-order/actual.json
```

加`--format json`可取得原欄位及JSON pointer。CLI只輸出stdout，不要求使用者搬檔、不建UI、不寫輸出檔；純函式不做檔案IO或匯入數值引擎。

入口[CONTRACT](CONTRACT.md)、[REPORT](REPORT.md)、[最終保存結果](after-final/summary.json)、[部分成交白話表](after-final/partial-pending/readable.txt)、[取消後白話表](after-final/settled-cancelled/readable.txt)。initial與tests-initial.log為補齊停止理由及未知status防護前的保存結果；after-final才綁最終source。未呼叫舊producer，舊0.8／0.2等結果原樣保留。

核准欄只指原保存合成研究單量，不是新的追加或正式授權。原提案只列一次、拆單共用預算；原單重評不變新批，新order另列。帳戶現金與權利照原row列一次；每單預留不能加回現金。待交割缺逐筆金額就null，已到日期缺結清journal仍UNKNOWN。
