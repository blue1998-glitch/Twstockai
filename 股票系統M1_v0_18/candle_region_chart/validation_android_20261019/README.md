# 0.4外框差異驗收啟動（2026-10-19 Work）

接續分支dev/m1-v018-chart-annotations，交接cf3b521b7a1280115228391d62839468671f51c0；成品d83f92cb47fe581ee76ee05a6f944cd5abc56434。實際compare：分支與交接identical；交接較成品ahead1，merge base為成品。已確認包含兩者，無main／舊ZIP覆蓋。

## 本輪實際完成

依序實讀AGENTS、CONTINUE最上方、M1_V019_CANDLE_BOUNDED_REGION_HANDOFF全文、PROJECT_VISION與VISUAL_RULE_NOTES最新要求、candle_region_chart README及validation_20261019/驗收報告、交付README與完整WORK_HANDOFF、PACKAGE_VERIFICATION／SOURCE_HASHES／GitHub下載收據、Android最新台帳。另實讀指定0.3原圖觀察紀錄／visual-review及G1 review／facts、G2精確端點review／verification；0.3兩張原圖已於同一對話直接讀取並保存，未重索使用者原圖。

本輪從固定成品提交**實際重新下載**ZIP 4,372,484 bytes，SHA256 0a759763dbebf562fa009097de3dc580a5ea296dc307b048366eaf0c0ca60cfc；HTML 36,783,169 bytes，SHA256 8642986a70a1c315046327b4ec97452eae19ba78fbe619a713ce2965de42d44f。CRC、內部SHA256SUMS與全部7成員大小／SHA逐一相符。源檔可讀標頭「M1 K線範圍區域主圖 0.4」。見download-verification.json。這是FILE_VERIFIED，不是手機執行通過。

先前GitHub收據145檔／56,224,224 bytes已實讀，所有equal／http200核視相符；本輪沒有重下載全部145檔。Codex398 Python／208 HTTP／44標籤／55操作／32外框為前輪實測報告，沒有移稱本輪跑過；本輪沒有完整checkout／bootstrap或產品執行。

## 直接讀取的保存工程圖片（與Android分開）

本輪另從固定提交下載並view_image目視，全部與SOURCE_HASHES逐一核對：
- validation_20261019/extents/before-G2-390.png與after-G2-390.png：前版全高底色跨三pane；新版價框包所選K線範圍、量框另在量pane，MACD無區域底色，來源標籤與縮放鈕仍在右側。
- after-G1-844.png：九月近似起緣／未閉合左邊、C後終點未定開放參照，量框另在量pane。
- clipped-G2-390.png：最高40.25畫外，未見假貼目前價軸頂的外框線；底框仍對應原低範圍，量框分開裁切。

以上只屬**ENGINEERING_IMAGE_OBSERVED**；不是本輪執行瀏覽器、Android原圖、手勢過程或使用者呈現認可。靜態圖亦不能證明所有縮放時均保持。圖片已在原提交保存，本輪不重複生成或編修它們。

## Android新增分項台帳

| 範圍 | 狀態 | 備註 |
| --- | --- | --- |
| 0.4手機身份／1101／新Raw／10/16／收27.30 | NOT_TESTED | 尚無本版使用者畫面或回報 |
| A：G2 136筆、35.90～40.25影線框、5/2代表點、量框分開、MACD無色帶及不遮擋 | NOT_TESTED | 已核原檔與保存工程圖，不能代填手機 |
| B：G1九月虛線／左緣未閉合、C後無假封閉框 | NOT_TESTED | 同上 |
| C：放大／移圖裁切不重算、不假貼邊、24月返486及分析10/16保持 | NOT_TESTED | 待最少操作回報，圖僅證當時畫面 |
| D：本版手機新JSON下載 | NOT_TESTED | 非本輪必要，不索舊JSON或先要求新檔 |

**0.4 Android仍NOT_TESTED_NEW_BUILD**；本輪沒有Android OBSERVED或USER_REPORTED，也無新手機BLOCKED。只驗A～C外框差異；不重開整套手勢／草稿／逐根流程。舊0.3-family PARTIAL_EVIDENCE_OBSERVED_VERSION_UNCONFIRMED及0.2部分證據保留，不沿用作0.4通過。

本輪下載／檔案核對未失敗；前輪新測試匯入失敗仍按工程報告保留。本輪未重試／繞過已知file://政策拒絕，未要求停用保護；無新手機開檔問題回報，不標手機受阻。

## 下一步仍同一Work

引導由固定ZIP下載，手機檔案管理解壓後開M1_v0_19_candle_regions_v04.html，自然回報0.4標頭與資料身份。先按G2價量帶，收一張能看到K／量／MACD與右側標籤／縮放鈕的新圖；只問這次外框是否符合需求。接著G1，再方便地放大／平移與返回24月回報C，不要求整套舊測試或大量新圖。只有確實驗手機下載精度才收0.4新原JSON。

G2日期已確認不重選；35.90～40.25只是display extent，不是正式壓力區界／分價／套牢持股。G1九月精確起日、C後終點、價格區界、整區量／量口徑、增量、自動分區選關、強度衰減及生命階段仍未定。Raw公司行動、五年Adjusted、歷史公布可得、資料缺口／SQLite未知根因與Darvas未完整讀限制全部保持。UI不當核心用途認可。

本輪僅新增驗收準備／下載核對／工程圖閱讀與待驗紀錄；沒有改產品、原引擎策略／庫／歷史／舊頁／案例／舊手機證據或main，無部署／付費／交易／訊息／子代理。新紀錄同分支實際保存並讀回確認後才宣稱GitHub已保存。
