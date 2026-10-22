# P1-7 研究核心完成節點（2026-10-22）

來源快照9dd0554f723cb598f9c88f2e0928dead28fa6166；此 SHA 是輸入來源，不是本文件最終出版 SHA。先查指定分支最新，不覆後續。

已實作且測試通過：獨立 core／loop／外部 store／CLI，18個定向 unittest。420個方案（70組配對×6）、216成本／可用現金敏感度方案已算；2個40筆不足明示。4個連續帳戶閉環實驗已跑，非拼接報酬。最終視覺報告與瀏覽器驗收在後續節點接續。

本環境已實際 bootstrap 成功：545補缺，7個既有差異保留、baseline_verified=true。首個 bootstrap 呼叫早於 sparse checkout 完成而找不到腳本，checkout 完成後重跑成功；首輪資料發現兩筆無報價，已改成 null 並加拒絕測試，沒有補行情。驗收 log 另存，舊歷史測試未重跑。

現況核對：`src/structure.py`、`src/period_ma.py`、`product_candidate/macd.py`、graph_core等可保留為獨立數值來源；正式關鍵價／全市場篩選品質尚未核。現有 analysis／period_store 保存分析結果而非持倉；manual_basis/store.py 已有不可覆寫選擇紀錄可借鏡。本輪掃描src／product_candidate／manual_basis及現有交接，未找到可沿用的持倉、現金、成交或換股資本帳。新 rotation_research 僅研究帳戶與結果檔，非正式持股系統／券商同步。沒有修改或升級舊 store schema。

研究完成但未通過投資驗證：所有真實結果受公司行動／公布時間／日曆與日OHLC成交限制，只是條件式扣成本價格報酬。未決比例、事件、參照重要性與正式風險限制不轉批准規則；結構UNKNOWN、交易false、rotation_policy NOT_APPROVED；飛輪投資價值NOT_VALIDATED。

尚未完成：股利／配股／減資的逐日資金帳、完整官方事件與普通股主檔／日曆、真正未見獨立樣本、上櫃及全市場、實體Android新頁。正式全換／分批取捨仍需研究證據後人工裁決，目前不要求使用者猜比例。

下一節點：完成中文圖表報告、讀回保存結果與瀏覽器小螢幕／放大檢查，再保存同分支。讀README與generated/design.json即可重現，不重新研究P0-1～P1-6已答原則。
