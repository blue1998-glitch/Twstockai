# Work 接續：人工口徑 0.1 後的核心工作

儲存庫 `blue1998-glitch/Twstockai`，分支 `dev/m1-v018-chart-annotations`。本輪起始 `5282b0803b928cc7c0f5400a78c1d0f39399e54b`；寫入前確認遠端新增 `1f12d64f279d26aeb19313d94570f6ed9a204912`，已閱讀並 fast-forward。最終提交以 HEAD 與 GitHub 回讀為準，勿以此處預填 ID 或改 main。依序讀根 AGENTS、CONTINUE、M1_V019_GRAPH_CORE_RESUME_HANDOFF，最新有效交接與此檔；若後續提交更新，查 commit 與測試證據。

本輪真正完成：原 0.4.3 完整 interned 數值位元組保持；獨立人工 Raw／Adjusted 候選主圖、6,344 保存 frame 精確 catalogue、純來源解析器和外部不可覆寫選擇 journal、切換股票維持人工模式、缺資料拒絕 fallback、localStorage 恢復及下載 JSON。4 Python tests 與真實 headless Chrome HTTP 主要路徑通過，1101 Raw／8069 Adjusted 匯出 `saved_selection` 與原 oracle 逐欄相同；390px 模擬無水平溢出。詳見交付 README、子專案 README／驗收報告、build-report及 SHA256SUMS。沒有新數值／策略／還原因子計算，沒有 Android 實機驗證。

資料界線：1101／2884 沒有保存 Adjusted；6488／8069 只有 2025-08-01～2026-09-30 的 283 根現金事件候選，完整公司行動／方法版本及歷史當時可得未核。五年 Raw 最新保存 2026-10-16，非即時。選擇時間是現在的人工意圖，歷史時點的人工選擇永遠不倒填。B 使用者仍未指定 Raw／Adjusted；大盤空頭不由自動指標決定此模式。分類 NOT_VALIDATED、核心用途 NOT_ESTABLISHED、交易資格 NOT_EVALUATED、historical_signal_eligible=false；資金閉環飛輪遠未完成。

本輪工作時遠端新增的 `docs/visual-discussion/20261022_user_simulated_multilevel_box_evolution/README.md` 是使用者人工多層箱型判讀：紫色舊大箱／褐色後繼大箱的時間演化、褐色含灰色小箱的層級關係。原圖是模擬，沒有精確行情或已核公式；最重要未決是兩個大箱底的來源與包含規則。下一步 Work 可針對該圖只討論真正尚未決定的箱底與關係，持續用已存真實案例驗證；不重問 B 口徑、1/27／G2 日期或已答高點，不憑圖添加固定幅度／天數／OSC 門檻。持續研究完整公司行動鏈與資料資格，之後再擴充全市場及換股資金閉環。若有新版 Android，區分實際使用者回報、下載內容核對與未測；不得把瀏覽器模擬冒充實機。

專案源碼在 `股票系統M1_v0_18/manual_basis/` 與 `manual_basis_chart/`，測試 `tests/test_manual_basis*`；舊 `pressure_chart`／`soft_region_chart_v043` 未改。所有前輪研究與正式交易策略原則保持。下次建議 Work 接續核心圖形判讀；大規模程式深化可交 Codex。無需因新對話重建父版或重做圖片研究。
