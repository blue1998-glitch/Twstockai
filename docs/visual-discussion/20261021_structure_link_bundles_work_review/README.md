# M1：按截止日整合觀察，研究局部價帶連結較大結構

2026-10-21 Work；分支 `dev/m1-v018-chart-annotations`；前核提交 `9afc83d5d827191c513e320bdfb89d0830c7c984`。最高目的仍是資金增值閉環＋正向資本成長飛輪；本輪沒有評估績效或交易行動。

先看 [三頁圖冊](output/pdf/m1-integrated-observation-bundles.pdf)，再讀 [局部與較大結構研究](STRUCTURE_LINK_RESEARCH.md)。新結論是：原構成來源的結束日不能直接當較大結構的終點或參照失效日；可以把內部移動、框外活動與返回，連到保留的較大背景，但尚不足以選正式父子或合併。

23個指定截止觀察已把原參照、局部活動、來源重用／全新、離開返回與目前位置合看。整合發現的39組缺比較、22筆追蹤及26組後續連結已依既有定義另存補充；22筆原截止前內容保持，舊檔案不改。人工確認是獨立事後閱讀層，未拿來訓練或回填歷史判斷。ABC人工39筆與6/13研究48筆明分。

| 檔案 | 用途 |
| --- | --- |
| `observation-bundles.json.gz`／`summary.json`／`query-specs.json` | 最終23個指定觀察；無唯一主範圍選取 |
| `baseline-*`／`storage-verification.json` | 補充前檢查點與23個完整物件無損轉存證據，不冒充最終hash |
| `evidence-extensions.json.gz`／`extension-summary.json` | 39比較、22追蹤、26後續連結；本次從保存原值補算，非歷史原快照 |
| `structure-link-cases.json`／`structure-link-verification.json` | 指定參照對照、可用性遮罩與事後人工範圍閱讀核對 |
| `manual-review-overlay.json` | 人工已答，知識日期2026-10-21，只供事後顯示 |
| `verification.json`／`source-provenance.json` | 新研究驗證、7來源指紋；不含產品分類器或Android驗收 |
| `figure-readout-data.json`／`figure-build.json`／`manual-qa.json` | 三頁圖面案例與最終PDF／PNG指紋 |
| `WORK_LOG.md`／`WORK_HANDOFF.md` | 真實執行次數、完整接續與來源恢復條件 |

`formal_interval/start/end/membership/parent/merge/selected_role/primary_pressure_id/historical_selection_time`仍null，`historical_signal_eligible=false`。分類器NOT_VALIDATED、用途NOT_ESTABLISHED、行動與飛輪成效NOT_EVALUATED、新版Android NOT_TESTED_NEW_BUILD。原10/7 core snapshot／numeric_frame仍無，不補造。

繼續Work研究較大結構持續角色與內部移動／另段活動的條件。保留所有原值、原策略參數、舊圖及後續成果，不改main，不部署、付費、自動交易、發訊息或開子代理。
