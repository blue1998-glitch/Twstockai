# 圖形辨識核心續接：執行環境阻擋（2026-10-19）

最新使用者要求：「繼續，要完成最重要的圖形系統」。本輪未完成核心，沒有將圖片首輪判讀或主圖樣式當作辨識完成。

## 實際節點

已確認分支前節點4f1769b654b57111f72d992739f76d85a9c877db；以GitHub讀到最新文字及實際數值程式。保留圖片學習已完成工作，沒有重下載／重讀101張原圖。實讀程式顯示缺口是自動辨識有意義的跨尺度箱型及主壓力階層；attempt_evidence仍要求人工參照。

## 環境與失敗

目前無本地Git checkout。復原原bootstrap及handoff至隔離暫存，實跑--hydrate-missing，exit2，PREPARATION_FAILED：Baseline ZIP missing or changed: M1_v0_17_01.zip。GitHub fetch_file回傳無可用二進位內容；fetch及fetch_blob分別拒絕非UTF-8。未恢復三份原始ZIP，沒有852檔基準通過。

根AGENTS第1–3點要求準備成功後工作，且「PREPARATION_FAILED means stop and inspect the explicit error」。因此停止產品源碼修改／執行，只依使用者保存續接要求記錄此阻擋。未刪檔、改驗證程式或用新小ZIP冒充歷史基準。錯誤細節見[environment_report.json](docs/core-recognition/20261019_resume/environment_report.json)。

未新增核心、沒有新Python／Chromium產品測試或新Android證據。先前圖片庫8項及索引14項、舊M1測試保持原輪資格，不沿用作本輪通過。核心NOT_ESTABLISHED、分類NOT_VALIDATED、行動NOT_EVALUATED。

## 下一步：Codex

需要能取得完整Git checkout與三份歷史ZIP的Codex環境。準備成功後新增獨立純數值候選，不修改原引擎；以最新收盤回看左側，處理跨尺度箱型、價量反證與失敗路徑，接入可放大真實圖。研究設定明示，人工案例不冒充自動結果，未定條件不補為批准門檻。

完整可貼指令：

```text
請接續股票系統M1，完成可執行的圖形辨識核心，而非繼續重畫樣式或只寫文件。

儲存庫：blue1998-glitch/Twstockai
分支：dev/m1-v018-chart-annotations
已確認前節點：4f1769b654b57111f72d992739f76d85a9c877db
先取此分支最新狀態，確認包含前節點並保留後續成果；不用main或舊ZIP覆蓋。

先讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md、docs/core-recognition/20261019_resume/environment_report.json、PROJECT_VISION.md、M1_V019_VISUAL_RULE_NOTES.md、M1_V019_IMAGE_LEARNING_HANDOFF.md及專案AGENTS。此Work環境無Git checkout，GitHub文字可讀但binary ZIP不可取；已在隔離恢復暫存實跑原bootstrap，exit2：Baseline ZIP missing or changed: M1_v0_17_01.zip。這不是完整checkout或852檔基準驗證成功。請在實際Git checkout執行python3 codex/bootstrap_m1.py --hydrate-missing，準備成功後依專案指示工作；失敗先診斷，不改指紋／刪檔強過。

已有成果不可重做：Drive第一批101原PNG、91去重首輪判讀與13單張複讀、特徵契約／失敗資格／可恢復v2 ZIP，均已保存；不是訓練完成。不重下載或重讀全部圖片。私人原圖／逐圖內容留Drive，不進公開Git。0.4.3底色樣式已由使用者回報接受，不再重開。

已實讀程式缺口：src/structure.py=structure-0.3-research，既有ATR／反轉候選及pivot區域不等於有意義跨尺度箱型；product_candidate/attempt_evidence.py必須人工near_high／left_zone，不會自動找代表或主壓力；macd.py是可重用獨立數值候選。保留原引擎、策略、schema、庫、歷史、舊頁及案例。新增版本化獨立純數值核心，UI只讀結果。

核心方向：以所選分析日的最後一根真實收盤為錨，由右回看左側高低點／箱型與相關支撐壓力；比較大帶與局部箱，不逐一任意切小箱、不以最近或最高或總量單條規則代替重要性。找幾何結構後才依相對位置及價量提出沉澱／轉強／破底候選；不能命名全段平緩帶或底部。提供來源證據、反證、缺證、失效及當時可知時間。未定公式可用明示研究設定與拒判，不升格使用者批准策略。人工案例與演算法產出分開，禁止以寫死答案冒充自動辨識。

已確定案例不再追問：
1. 1101新官方Raw，已存分析日2026-10-16收27.30，非即時行情。1/27指2026-01-27高26.95，使用者認為較重要；10/12越過、13跌回、14越過、15跌回、16再越過，保存失敗／重越，不稱確定突破。量比口徑分列，量增不等實際持股沉澱。
2. 2025-06-03高28.00屬前箱破底K、使用者排除現箱；保留原值，不能推所有破箱K皆自動排除。6/4高27.45也不能刪掉以湊1/27為整窗最高。
3. 前箱2025-04-07～06-02含兩端39筆，5/13高31.40為已答局部代表；使用者指出2023-06～2025-04更大壓力帶更重要。主帶只到月份精度，完整月份顯示463筆／外包28.45～39.25不等正式成員或區界，不推大或舊永遠勝出。
4. G1原代表2023-11-28高35.50，約9月不確定起緣到C2024-01-19；G2精確2023-01-16～08-16的136筆，5/2高40.25。G2影線外包35.90～40.25只是顯示，不是正式壓力界。原端點OHLCV核對與舊證據不重索。C後終點未定，不固定4/30、不分類全部後續K。
5. 原①④、G1/G2/G3不覆寫；新代表1/27與原④1/29分開。

以同源真實資料做截短前綴／追加未來不回寫／資料缺漏／同價多點／假突破跌回／破底後新箱／跨尺度父子與衝突等測試。研究候選與已批准規則分開，缺歷史公布時間不得虛稱當時資訊完全可得。只做適合新改動的測試，不重跑無關舊功能。交付可放大、K量MACD同步的實際辨識結果與精確JSON，不以手動畫面充作自動核心完成。

正式區界、整區量與量口徑、增量、自動門檻、強度衰減、生命階段仍未定。Raw公司行動／五年Adjusted／歷史可得／資料缺口／Darvas完整正文未讀／SQLite未知保留。工程、Android、辨識品質、核心用途及交易價值分開，未測不填通過。

一般可逆工作直接做；不改main、不部署付費交易發訊息、不啟動子代理。完成源碼、成品、可重現測試、錯誤與限制、最新接續入口保存此分支並逐檔GitHub回讀確認。結束列實際完成／未完成、入口、提交與下一步Work或Codex。
```
