# 貼給Work：新版三關實機與用途驗收

貼上以下內容即可；進入時請讀取指定分支最新GitHub提交並記錄實際讀到的SHA，保留後續成果。最終交付訊息另附已確認的完整提交。

```text
請接續股票系統M1，驗收最新人工三關主圖，不只提出計畫。
儲存庫：blue1998-glitch/Twstockai
分支：dev/m1-v018-chart-annotations
已核實成品提交：87ec609ef51d7346554e2546e520a9dbc4ac2235，包含交接5713fe248915dc47030de8e7573e2751457a53c5及hurdle-chart-view/0.1工程；同目錄後續收據提交亦保留。先確認指定分支包含此提交；若有更新，讀最新交接並保留後續成果，不用main或舊ZIP覆蓋。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_1101_THREE_HURDLES_HANDOFF.md最新節、股票系統M1_v0_18/hurdle_chart/README.md及validation_20261018/驗收報告.md、M1_V019_PRESSURE_CHART_ANDROID_ACCEPTANCE.md最上方，再讀M1_V019_VISUAL_RULE_NOTES.md與docs/visual-discussion/20261018_1101_selected_hurdles.json。

成品入口：deliveries/m1-v019-three-hurdles-20261018/README.md。
請開新版小ZIP內M1_v0_19_three_hurdles.html，標頭M1三關主圖0.1；不是舊pressure或technical頁。預期1101／Raw｜新官方日線／2026-10-16、日收27.30、24月486根。

本輪已實作原①26.10／④26.85已過點價與後續G1 35.50、G2 40.25、G3 50.20分層，近期窗保留畫外／超軸提示、來源定位／返回、G3五日證據與精確JSON。365 Python通過；實際Chromium208個HTTP檢查通過，含100 oracle下載與另2次人工層核對。額外file://開檔被管理政策ERR_BLOCKED_BY_ADMINISTRATOR阻擋，整體報告PASS_WITH_BLOCKED_CHECK；這不是新版Android開檔通過。

先給我最簡單的手機操作引導，再依實際回報記錄：
1. 確認新頁版本／來源／分析日；直向與橫向看原①④、三關、超軸提示及近期K是否可讀。
2. G1定位到2023-11-28高35.50、G2到2023-05-02高40.25，分析日仍10/16；按24月回486根近期窗。「回近期」是60根，兩者別混稱。
3. G3證據保留五個50.20來源日，未指定唯一日；各日期可定位，長ID與JSON預設折疊。顯示錨不是替使用者選唯一日。
4. 檢查圖點證據、縮放／平移、游標及K量MACD同步；切10/15、其他股票或原來源時三關不套。記直橫／開檔方式／載入耗時及卡頓。
5. 收新版原JSON、主圖與G3證據截圖，實讀核對hurdle-chart-selection/0.1、manual_hurdles、G3.source_date=null、來源指紋與原數值精度。原案例的NOT_IMPLEMENTED是原時點歷史，新wrapper另有已接入標示。

新版Android仍NOT_TESTED_NEW_BUILD，舊pressure的PARTIAL_EVIDENCE_OBSERVED及原圖／JSON保留，不能沿用。區分直接觀察、使用者回報、原檔核對、未測；未收到證據不得代填成功。若工具不能讀GitHub或原檔，明說實際限制，不能把摘要當實讀。

主圖是否讓人理解目前位置、已過點價及後續三關，以真實圖形用途回饋為準，不把畫點線或測試通過當核心認可。區界／整區量／增量／強度／衰減／自動選關／生命階段仍未定；只有真正未定核心才用具體圖形詢問，不自行補門檻。

完整公司行動／歷史公布可得及五年Adjusted未完成，Raw舊高不認證校正後共同基底壓力，五年高不當全歷史高。TWSE六日Work補證尚未接產品稽核，TPEX待主證；其他缺口與SQLite未證實根因保留。

一般可逆工作直接處理，可重現工程缺陷交Codex並提供版本、來源／日期、操作、原圖與原JSON。保留原引擎、策略、庫、歷史與舊頁，不改main、不部署／付費／交易／發訊息／子代理。成果與實證保存同一指定分支並確認GitHub；不能保存就明說。

結束列出實際完成／未完成、最新提交、成品入口與下一步用Work或Codex。每次建議切換，都附可直接複製給下一模式的完整指令。
```
