# M1 真實跨尺度K線比較 0.1

新圖已直接接入1101完整真實K／量／MACD，原核心、參數、策略與歷史保持不變。**圖表工程完成，不等正式主壓力辨識獲認可。**

- [直接下載HTML](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/dev/m1-v018-chart-annotations/股票系統M1_v0_18/cross_scale_chart/generated/M1_v019_cross_scale_real_v01.html)：下載後開啟`M1_v019_cross_scale_real_v01.html`，無CDN或瀏覽器gzip需求。GitHub raw可能顯示文字，這不是部署網站。
- [下載小ZIP（749,695 bytes）](https://raw.githubusercontent.com/blue1998-glitch/Twstockai/dev/m1-v018-chart-annotations/deliveries/m1-v019-cross-scale-real-20261020/M1_v019_cross_scale_real_v01.zip)：解壓即有同一HTML、完整精度JSON及來源／核對收據。
- ZIP SHA256：`894d93f852edce18f741695b96766210702c51be8b961916520fd3d29464d6c8`；[CRC及6成員SHA](PACKAGE_VERIFICATION.json)、[外部SHA](SHA256SUMS.txt)。
- HTML **2,232,879 bytes**，SHA256：`f5b3b4e5e03da1c8291ff5854e0a6dfbb974286fe5cfbcb9a466ec6e138203ee`。
- [可直接讀取的完整資料JSON](../../股票系統M1_v0_18/cross_scale_chart/generated/comparison-data.json)、[來源取得收據](../../股票系統M1_v0_18/cross_scale_chart/generated/source-acquisition.json)、[實測及畫面](../../股票系統M1_v0_18/cross_scale_chart/validation_20261020/驗收報告.md)、[完整可貼Work指令](WORK_HANDOFF.md)。本輪遠端保存需以實際push／回下載收據確認，不沿用舊收據。

標頭「M1 真實跨尺度比較 0.1」，1101／Raw／固定2026-10-16收27.30，非即時。全1,213根2021-10-18～2026-10-16來自固定診斷成品，OHLCV／股數／MACD／SMA／source／basis／frame／prefix及原core全等，不用假行情或時間軸冒充K線。逐根無空值不代表完整日曆，原9個待核日期與基底限制保留。

手機使用：先看「跨尺度全景」，再選「主帶／拒絕串」「39筆／同幾何」「近期／反證」；＋−放大，預設拖曳查詢，選「移圖／雙指縮放」平移，按「返回近期」回24月。K量MACD與下方日期軸同步；選證據→定位來源及時點，或點日期查詢，分析日不變。圖下勾選可分開來源層，主圖短圖例持續辨色；長ID折疊。

人工月份主帶是463根月份閱讀外包、精確端點仍未知；B77／左右拒絕串／人工39筆／B44-B80同幾何／B88分別顯示。原6.05／3.5700／−2.4800及3.25／2.4675／−0.7825保持；來源末轉折、確認／判定、研究離箱與人工整箱終點不混同。人工對照是後來覆核，不作歷史自動訊號。

實際本輪7 Python PASS，最終47真實Chromium HTTP／12完整精度下載PASS，四尺寸、DPR1／2、原生單指／雙指操作、實際MACD像素不受來源底色影響、0JS錯誤／外部請求；28最終PNG。首次MACD欄位假設及18px日期軸錯位失敗、修正與較早畫面保留。未重跑無關35／60／398或舊驗收。

**未完成／未知**：原自動核心尚未完整重現人工主帶、39筆歸屬／六月後整箱；正式區界、量口徑／增量、強度衰減／重要性、合併／直接承接、生命階段未知，primary_pressure_id=null。89候選／84幾何組非獨立型態數，不等長觀察窗不作公平排序。Raw公司行動、五年Adjusted、歷史公布可得、原缺口／Darvas正文／SQLite未知保留。Android **NOT_TESTED_NEW_BUILD**、使用者開檔／裝置效能未測；file://不重試不繞過。此版只綁1101固定案例，不套其他股票或分析日。

下一步使用**Work**直接看新真實跨尺度圖與已答整體判讀的差異；不重讀101圖片、不重開0.4.3或舊Android按鈕。原頁／Work時間軸與舊成品全部保留，不改main、不部署付費交易訊息子代理。
