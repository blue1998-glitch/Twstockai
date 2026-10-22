# 最終交付：P1-7 獨立研究版本0.1

已實作且測試通過：core／loop／store／CLI；18 unittest、9982真實來源與帳務斷言、CLI RUN/READ逐位元相同。Chrome15136檢查，含390／1400、放大局部捲動、截止／事後切換、精確JSON與SVG下載；0JS錯誤／外部請求。9張PNG與9張向量SVG、繁中自足HTML及完整數值封包已生成。圖上標示的是實驗參照越過／返回與全換候選時點，非正式箱型強弱；分批時點逐筆列於報告。

420方案、216敏感度及4個連續帳戶；2個40筆不足拒算。起始最終設定20,000股A，25%對應5000股避免整張造成20%／30%近似；早期10,000股工程試跑不是最終研究結果，最終9982／36資格以generated驗證檔為準。源碼／測試先保存GitHub完成節點cf10dbdb8e8e3e6f59609dfe048e1daa7f5fc1c4，實際最終出版SHA以分支讀回及交付收據為準，不誤用輸入來源9dd0554f。

已完成研究但未通過驗證：所有條件式價格扣成本結果與全換／分批假說；不是真實總淨報酬、最適配置、全市場或資金飛輪驗證。公司行動未完備嚴格拒算；資料缺口與舊事件證據全部保持。正式結構／量角色未知、策略與交易不批准；Android實機NOT_TESTED_NEW_BUILD。

尚未完成：完整事件總報酬帳、普通股主檔與歷史日曆／公布可得、真正未見獨立驗證、上櫃全市場、正式持倉風控與Android。現在無需人工替研究猜比例；重要策略選擇留待合格證據。

建議下一階段Codex，接具體資料及會計工程。可直接貼：

```text
接續blue1998-glitch/Twstockai，分支dev/m1-v018-chart-annotations。先查最新SHA，確認包含cf10dbdb8e8e3e6f59609dfe048e1daa7f5fc1c4與其後P1-7最終交付，保留所有後續，不用main或舊ZIP覆蓋。讀根AGENTS、CONTINUE_IN_WORK_MODE、PROJECT_VISION、M1_V019_GRAPH_CORE_RESUME_HANDOFF，再讀rotation_research/README、WORK_HANDOFF、DATA_QUALIFICATION、RESEARCH_REPORT、generated/design與驗證檔。依根AGENTS實跑bootstrap並保留差異。
P1-7已實作core/loop/store/CLI，18unittest、9982來源帳務與前綴斷言、Chrome15136檢查及真JSON/SVG下載通過；420方案＋216敏感度＋4同帳戶閉環，2個40筆不足拒算。20,000股A；25/50%和20筆代理／量比前日／5筆延後／10筆檢討全是競爭實驗，不是使用者正式圖形策略。不能以此宣布分批勝出。
下一工作：先補可追溯公司行動事件表，區分公布可知／除權息交易／基準／發放，完成股利應收與可用現金、配股／減資會計，再對合格資料窗比較真正總淨報酬。保留RAW/Adjusted手動模式及同基底；缺失拒算，不默認無事件。補真正未見獨立期及上櫃時才擴大範圍。原P0～P1-6已答不重問，正式箱底／關鍵價／交易資格與配置比例仍未批准。不要重跑無關舊驗收。原引擎庫資料舊圖／main保持；不部署付費、訊息、自動交易或子代理。逐節點保存指定分支，CAS確認最新父提交，提交後SHA與內容讀回。
```

以下為早期完成節點，保留歷史：

---

# P1-7 研究核心完成節點（2026-10-22）

來源快照9dd0554f723cb598f9c88f2e0928dead28fa6166；此 SHA 是輸入來源，不是本文件最終出版 SHA。先查指定分支最新，不覆後續。

已實作且測試通過：獨立 core／loop／外部 store／CLI，18個定向 unittest。420個方案（70組配對×6）、216成本／可用現金敏感度方案已算；2個40筆不足明示。4個連續帳戶閉環實驗已跑，非拼接報酬。最終視覺報告與瀏覽器驗收在後續節點接續。

本環境已實際 bootstrap 成功：545補缺，7個既有差異保留、baseline_verified=true。首個 bootstrap 呼叫早於 sparse checkout 完成而找不到腳本，checkout 完成後重跑成功；首輪資料發現兩筆無報價，已改成 null 並加拒絕測試，沒有補行情。驗收 log 另存，舊歷史測試未重跑。

現況核對：`src/structure.py`、`src/period_ma.py`、`product_candidate/macd.py`、graph_core等可保留為獨立數值來源；正式關鍵價／全市場篩選品質尚未核。現有 analysis／period_store 保存分析結果而非持倉；manual_basis/store.py 已有不可覆寫選擇紀錄可借鏡。本輪掃描src／product_candidate／manual_basis及現有交接，未找到可沿用的持倉、現金、成交或換股資本帳。新 rotation_research 僅研究帳戶與結果檔，非正式持股系統／券商同步。沒有修改或升級舊 store schema。

研究完成但未通過投資驗證：所有真實結果受公司行動／公布時間／日曆與日OHLC成交限制，只是條件式扣成本價格報酬。未決比例、事件、參照重要性與正式風險限制不轉批准規則；結構UNKNOWN、交易false、rotation_policy NOT_APPROVED；飛輪投資價值NOT_VALIDATED。

尚未完成：股利／配股／減資的逐日資金帳、完整官方事件與普通股主檔／日曆、真正未見獨立樣本、上櫃及全市場、實體Android新頁。正式全換／分批取捨仍需研究證據後人工裁決，目前不要求使用者猜比例。

下一節點：完成中文圖表報告、讀回保存結果與瀏覽器小螢幕／放大檢查，再保存同分支。讀README與generated/design.json即可重現，不重新研究P0-1～P1-6已答原則。
