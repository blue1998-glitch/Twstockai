# 0.3 Android新增差異：驗收啟動（2026-10-19 Work）

成品提交31d80971b265942eb3d7573fddf00f6782f20a55；接續c96195ba52cda852ce8473bdadd10071087afb11。當時分支與交接identical，交接較成品ahead1且merge base為成品，已確認包含兩提交。未用main／舊ZIP覆蓋，未改產品或原證據。

## 本輪實讀及執行

依使用者指定順序實讀AGENTS、CONTINUE最上方、人工區域交接最新節、PROJECT_VISION與VISUAL_RULE_NOTES最新要求、region_chart README及validation_20261018/驗收報告、交付README、完整WORK_HANDOFF、PACKAGE_VERIFICATION、SOURCE_HASHES、GITHUB_DOWNLOAD_VERIFICATION、Android台帳最新紀錄，以及G1 user_review／facts、G2 endpoints user_review／endpoint verification。舊文件「尚無0.3」為前輪歷史，以最新Codex已實作節為準。

本輪實際從固定成品提交GitHub下載4,371,652 bytes ZIP，SHA256 ef258e1dfa1bd965168f630c642b56475cc132fc7184b85dbbfe999e1fde2f9b相符。讀取解壓成員及CRC、內部SHA256SUMS、全部7成員大小／SHA與交付契約相等。HTML36,744,203 bytes，SHA256 0a1513b361c1473c4e38bb3c5db2f3477054fe2bb4779592f31b5b73fc84bb8e；直接源碼讀到標頭「M1 價量區域主圖 0.3」。詳見download-verification.json。這是FILE_VERIFIED／直接原檔核對，沒有執行頁面，不當Android OBSERVED。

舊GitHub收據129檔／55,089,638 bytes，逐項http200及equal為true，已實讀並檢視；本輪只重新下載核上述小ZIP，沒有重下載全部129檔。383 Python與208／44／55 Chromium為先前Codex報告，本輪沒有重跑；沒有完整checkout／bootstrap或產品測試需要。

## 分項台帳（尚無本版手機新證據）

| 新差異 | Android狀態 | 證據 |
| --- | --- | --- |
| 0.3開檔身份、1101新官方Raw、分析10/16、收27.30、24月486根 | NOT_TESTED | 尚無使用者新畫面或回報；只核成品源檔 |
| G2時間帶1/16～8/16、5/2高40.25、端點OHLCV證據 | NOT_TESTED | 待新主圖及區域證據 |
| G1約9月不確定起緣→C、原11/28高35.50、返回24月不改分析 | NOT_TESTED | 待回報；精確起日仍未定 |
| 查詢不移窗、明選移圖／雙指、直橫K量MACD同步／遮擋 | NOT_TESTED | 靜態圖不當操作或旋轉保持 |
| 查詢1/16→1/17→1/30跨休市 | NOT_TESTED | 待實際操作回報 |
| 草稿起終點／複製／下載／狀態／逆序與重開、切來源／分析日清空 | NOT_TESTED | 只有要核手機下載才收新版原JSON |

0.3 Android整體仍NOT_TESTED_NEW_BUILD。OBSERVED、USER_REPORTED尚無新增；手機BLOCKED亦無新回報，不憑舊環境錯誤判手機受阻。

## 失敗與未測

本輪第一個原檔標頭檢查錯誤要求「主圖0.3」中間無空格，assert失敗；此前ZIP與HTML SHA已相等。直接查看原始header確認實際有空格，修正核對假設後重新完整核ZIP／成員。不是產品FAIL、沒有更動成品來滿足測試。失敗摘要保留在JSON，不把初次失敗刪除或宣稱首輪全通過。

原file://政策阻擋為舊雲端環境KNOWN_BLOCKER，本輪未重試／繞過、未要求停用保護。本輪沒有瀏覽器／Android執行、新手機JSON、效能或核心用途驗證。手機新錯誤需按實際機型／開檔方式／錯誤另記。

## 下一步：同一Work先收G2

引導使用者由固定ZIP下載、手機檔案管理解壓後開M1_v0_19_manual_regions_v03.html，核實際0.3標頭及來源／日期／收盤／486根；按G2價量帶看主圖，再按區域證據。最少收新版G2主圖及端點證據畫面；可先用文字回報身份，不要求再傳舊0.2或0.1檔。沒有回報前維持未測。之後依WORK_HANDOFF B～E繼續，不一次索取大量畫面。

G2日期已確認不重選；G1精確起日、價格區界、整區量／量口徑、增量、自動分區／選關、強度／衰減／生命階段未定。C後終點未知，不固定4/30或分類所有後續K。Raw公司行動／五年Adjusted／歷史公布可得、資料缺口／SQLite根因及Darvas正文未完整閱讀狀態保留。原0.2 PARTIAL_EVIDENCE_OBSERVED及已收束標籤驗收不變，UI不代表核心用途認可。

本輪只保存新驗收啟動、文件實讀／本輪下載核對與待驗清單，同分支確認GitHub後才宣稱保存。原引擎／策略／庫／歷史／舊頁／證據／main不改，沒有部署、付費、交易、訊息或子代理。
