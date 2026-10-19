固定0.4.3成品提交：ba78194d5b385324be76c026ba499eedd32c4647；新ZIP已實際從GitHub下載核SHA／CRC／內部SHA，與PACKAGE_VERIFICATION及最終32項HTTP報告合計3檔核對通過。[本次實際下載收據](deliveries/m1-v019-soft-regions-v043-20261019/GITHUB_DOWNLOAD_VERIFICATION.json)。原38檔全面回讀於工作區維護清理後無法確認收據，不宣稱已完成；成品／源碼／證據已先保存GitHub，不受本地清理影響。最新交接以本檔所在分支提交為準。

# 2026-10-19 最新：0.4.3背景與K線須同時清楚

使用者原話：「已經看的見了，顏色可在深一些標準是能一眼辨識背景卻也能清楚看見K線兩者必須能清楚分別辨識。」上一0.4.2語境已能看見，屬USER_REPORTED_REGION_VISIBLE_WITH_DARKER_REQUEST；重送只記一次。沒有新圖或裝置／實開版號獨立確認，不升級完整Android驗收。標準是背景一眼可辨、K實體與影線同時清楚。

新增獨立soft_region_chart_v043，預設18%不透明度、較淡12%／明顯26%，背景先畫、K／量原色與100%前景保持。仍無區域框、原範圍與數值不變、MACD不染色。實際32項Chromium133 HTTP PASS，24組前景繪製／101067純色像素核對，16張工程圖保存並目視G2-390／G1-844；payload無損與ZIP CRC／SHA通過。首次啟動太早及像素假設失敗保存並修正，沒有改產品迎合測試。整套Python／舊完整回歸未重跑。

[成品入口](deliveries/m1-v019-soft-regions-v043-20261019/README.md)、[完整可貼Work指令](deliveries/m1-v019-soft-regions-v043-20261019/WORK_HANDOFF.md)、[32項／失敗修正／限制](股票系統M1_v0_18/soft_region_chart_v043/validation_20261019/驗收報告.md)。遠端保存以實際提交後收據為準。

0.4.3 Android NOT_TESTED_NEW_BUILD。下一步仍同Work只看新版預設顏色，無須重測舊功能或索舊圖JSON；工程通過不是核心用途認可。全部原策略／來源未知與file://阻擋保留，不改main、不部署付費交易訊息子代理。

---

# 2026-10-19：底色太淡，0.4.2已實作待使用者新觀感

使用者最新原話：「看不到底色區域」。無本輪新圖，裝置與實開版本未獨立確認；不稱新Android成功或直接觀察。舊0.4範圍認可與無框需求保持，0.4.1的3%底色尚不足以獲使用者認可。

新增獨立soft_region_chart_v042，預設12%不透明度，較淡8%／標準12%／明顯20%。這是可逆UI濃淡，不是策略。原全選段範圍／價量各自填色／MACD無染色／G1起緣漸淡／C後未知／無邊框／原來源點與關卡線保持。固定0.4.1父ZIP核SHA，完整payload僅view_version／artifact_id更新。

本輪實際28項Chromium133 HTTP PASS、16張前後／裁切工程PNG與CRC／SHA包裝核對；已目視G2-390／G1-844，底色可見。不是實體Android或核心用途通過，整套Python及舊完整瀏覽器測試未重跑。詳細來源、測試字體條件、狀態與限制在[新報告](股票系統M1_v0_18/soft_region_chart_v042/validation_20261019/驗收報告.md)。

[成品入口](deliveries/m1-v019-soft-regions-v042-20261019/README.md)，[完整可貼Work指令](deliveries/m1-v019-soft-regions-v042-20261019/WORK_HANDOFF.md)。固定成品提交0aa3cd3c32da7c494f48e6b672cbc7319f4ff7e8。已從GitHub固定提交實際下載核對36檔共5,810,763 bytes，ZIP CRC／內部SHA及指定0.4祖先提交核對通過；[遠端收據](deliveries/m1-v019-soft-regions-v042-20261019/GITHUB_DOWNLOAD_VERIFICATION.json)於成品後交接保存，最新交接以本檔所在分支提交為準。

下一步仍同Work，只看新底色是否清楚／不遮K；原Android狀態NOT_TESTED_NEW_BUILD，不索舊圖或JSON，不重開舊功能。已知file://阻擋不重試或繞過。保存全部舊成果，不動main，不啟動子代理。

G2 2023-01-16～08-16／136筆及35.90～40.25只作原全選段顯示外包，非正式壓力區界或分價持股；原5/2／40.25代表點保留。G1精確起日未知，九月起緣漸淡，不把9/1當正式起日；C後終點未知，不固定4/30或分類全部後續K。整區量／量口徑／增量／自動分區選關／強度衰減／生命階段仍未定。Raw公司行動、五年Adjusted、歷史公布可得、原資料缺口與SQLite未知根因保持；Darvas箱型正文未完整讀取。UI接入不是核心用途認可，核心用途NOT_ESTABLISHED、分類NOT_VALIDATED、行動NOT_EVALUATED。
