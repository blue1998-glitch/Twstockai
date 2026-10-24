# 公司分項來源研究0.9：成品與實測入口

本輪重用同一公開說明書，新增兩頁已核公司分項與同家族對帳，精確嵌入完整0.8；個人權利／淨額與策略資格保持未知，所有舊原件／程式／庫／歷史／成品及main保留。

- [直接下載ZIP](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-capital-components-20261023/m1-capital-components-v09-20261023.zip)
- [GitHub檔案頁](m1-capital-components-v09-20261023.zip)：可按Download raw file。
- [SHA256SUMS](SHA256SUMS)、[封包收據](bundle-receipt.json)、[全新解壓驗收](package-verification.json)。
- [實作與實測報告](../../股票系統M1_v0_18/rotation_research/capital_components_20261023/REPORT.md)、[來源契約](../../股票系統M1_v0_18/rotation_research/capital_components_20261023/CONTRACT.md)。
- [完整可貼Work唯讀續接指令](../../股票系統M1_v0_18/rotation_research/capital_components_20261023/WORK_HANDOFF.md)。
- 固定工程逐檔GitHub原bytes回讀見 [GITHUB_READBACK.md](GITHUB_READBACK.md)／[JSON](GITHUB_READBACK.json)，以實際收據為準。

`m1-capital-components-v09-20261023.zip`：32,335,922bytes、723成員，低於32 MiB。SHA256：

```text
9a97f1aff7ad1b37da2249948ccaf62662b5af4ad9d9e3260907cecb426d8571
```

原0.8的693成員逐位元保留，十一層manifest有效，新manifest核722其他成員。解壓到全新目錄後依CAPITAL_COMPONENTS_START_HERE.md以標準Python離線重現；無需網路、PDF工具或瀏覽器。此非完整checkout，不以舊包覆寫專案。

本輪29新＋實跑0.8相關31＝60通過，與前輪31新＋29回歸的60不同；新解壓同60與producer通過不累加120。實核122原價量檔／16日曆，按實際輸入重算70拒算／2不足／8換股影響未支援／合格總淨報酬0；daily／journal空、numeric replay／六方案0，缺價診斷精確等parent。

新三筆是公司股東、員工及董事會計算參照來源觀察：160200＋18000＝178200仟股，N1股本180000＋公積342900＝總權益522900仟元；僅同一增資來源家族對帳，新增交易事件與獨立市場樣本0。29.05元保留計算參照角色，不補Raw或估值，不由總額或年末股數推個人比率。parent原null保持。

官方新原件／官方與原PDF GitHub請求均0；重抽／視讀391印刷11、456印刷76，xref警告及首個parser失敗／修正保留。765頁未全書核閱，Work附件／meta仍未取得／未讀，Work本機重用時間只記使用者陳述，不補舊Work GitHub未知時間。個人實配／畸零／可賣日／淨收／期初權利與完整行動覆蓋等仍缺，無新UI或Android驗收。下一步Work只來源研究與GitHub唯讀，後續工程仍原既有唯一Codex；不部署、付費、交易、訊息或子代理。
