# M1線標籤修正版0.2下載

請開新檔 **M1_v0_19_three_hurdles_labels_v02.html**，頁頂「M1 三關主圖0.2」。原0.1的HTML／ZIP／實機原圖與JSON保留，不拿舊檔代替新版差異驗收。

- [直接下載修正版小ZIP](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-v019-hurdle-labels-v02-20261018/M1_v019_three_hurdles_labels_v02.zip)
- [ZIP SHA256](SHA256SUMS.txt)／[CRC與解壓逐檔指紋](PACKAGE_VERIFICATION.json)
- [可見修正前後畫面](../../股票系統M1_v0_18/hurdle_chart/validation_labels_v02_20261018/前後畫面.md)
- [本輪實測報告](../../股票系統M1_v0_18/hurdle_chart/validation_labels_v02_20261018/驗收報告.md)／[使用及重現](../../股票系統M1_v0_18/hurdle_chart/README.md)
- [貼給Work的驗收指令](WORK_HANDOFF.md)／[新版手機差異清單](../../M1_V019_PRESSURE_CHART_ANDROID_ACCEPTANCE.md)

小ZIP **4,358,779 bytes（約4.16 MiB）**，SHA256 `cfe933d036c7f55b02d4e4f15d20485976a2b1c0edfe95a2b9385c13d3d0687f`。HTML **36,714,312 bytes**，SHA256 `fe0d27111f9a03b23ea587cb195a5b5b3987b4862e7af6ee20684be1b69fbce6`。ZIP含完整離線HTML、原人工案例、簡短說明及內部SHA，不需連網載行情。

新1101Raw／10/16／收27.30，近期24月486根；來源2023-11-28畫外，但價位在軸內的G1 35.50現在可在主圖右側辨認並點選證據。線標籤／來源圓點分離，刻度／K／縮放鈕分區；G2／G3超軸不假貼邊、不擴價軸。標籤點選不跳分析日／游標；定位來源才明示移圖，24月可返回。原①④、G3五日／未指定唯一日及後來人工覆核資格不變。

本輪實際：**10項Python專項PASS**、**208項真實Chromium HTTP回歸PASS**（100次完整oracle下載與另2次人工層下載）、**44項標籤專項PASS**，四種視窗有實際前後圖。舊整套365是上一輪，未冒充本次全測。已核244官方原檔／4854新Raw／1490原時點，新下載較已核對手機JSON只改view_version，來源／數值／精度不變。

**0.2 Android NOT_TESTED_NEW_BUILD**，原0.1 PARTIAL_EVIDENCE_OBSERVED證據保留，不重要求同版相同圖／JSON；Work先收新版G1標籤閱讀與點擊不跳日差異。原file://管理拒絕本次未重試／未繞過（PASS_WITH_KNOWN_BLOCKER），不是新版本機開檔通過。

區界、整區量、增量、強度、衰減、自動選關、生命階段未定；完整公司行動／歷史公布可得／五年Adjusted未完成。Raw舊高不認證共同校正壓力、五年高不是完整歷史高，其他資料缺口／SQLite未知根因保留。原引擎／策略／資料庫／歷史／舊已交付頁與main不改，沒有部署、付費、交易、發訊息或子代理。

GitHub實際保存與下載核對以同目錄GITHUB_DOWNLOAD_VERIFICATION.json為準；沒有收據前不把本地結果當已下載驗證。
