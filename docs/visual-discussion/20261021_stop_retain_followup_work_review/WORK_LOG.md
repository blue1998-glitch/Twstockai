# 本批實際作業紀錄

起點 f34635187baf0efa0c9d66d5884e06b114fd95c7，分支dev/m1-v018-chart-annotations；交接日期沿客戶端2026-10-21台北時間，不採不一致主機時鐘。已讀指定三根入口最新節、上批WORK_HANDOFF、PROJECT_VISION與G2原裁決，保留完整歷史前鏈。

1. 核既存2884／1101來源與上批生成函數SHA，沒有抓行情或覆蓋來源。比較首次收盤離開、返回與之後整根離開，先發現ABC相符，再以G2早期同類事件否定強制通用停止。未新增使用者提問或標籤。
2. 新branch_research.py driver實際1次，重用未改propose函數，六池243觀察、633分支；指定起日只作外部範圍驗證，不塞入自動候選生成。新verify_branches.py實際1次，2284事件、633分支、208去重逐截止及六範圍污染／價格變換、合成事件通過。這不是生產分類器測試。
3. Driver在首次執行後補上輸出deterministic gzip以方便保存完整池，語義未改，未為此重跑driver；驗證腳本實際產生gzip，282244 bytes，回解壓等於完整原JSON。大原JSON只留可重現中間檔，不把不完整摘要當全池。
4. 新build_figures.py成功執行2次。首稿頁2／3標註碰面板邊界，降低標註位置後重畫；頁1內容保持。兩次批次Poppler渲染後，最終頁2已看，頁3第一次載入失敗。PIL診斷該PNG僅90112 bytes、截斷；PDF本身3頁有效。單獨重渲染頁3到暫存位置，PIL檢查後複製、fsync、讀回逐bytes相等再驗，137536 bytes，再成功人工檢視。根因NOT_ESTABLISHED，不把推測寫成已診斷原因。原歷史圖冊重建0次。
5. 三頁最終靜態圖均人工看過，最終PDF SHA e6d6a98134ba6803b9e0ec835bc94cf2f7cb68cdc3bc16e12e5baa3721174a5b；人工QA綁定最終PDF／PNG。這不是手機瀏覽器或Android實測。verification.json的圖冊狀態在最終檢視後更新；若重跑數值驗證會重設為未作圖，必須重新綁定新圖QA。
6. 追加新根入口，保留全部舊文字；同分支保存，再固定提交全文／二進位回讀，結果另存GITHUB_READBACK.json。實際提交以該收據與HEAD為準，未記成未來已成功。

原核心、MA/MACD/pivot/box/reaction、adapter/source-query CLI、bootstrap、原14/22/60及舊產品測試均未重跑，前批362檢查也未重跑；沒有部署、付費、交易、訊息或子代理。Android NOT_TESTED_NEW_BUILD，分類NOT_VALIDATED，用途NOT_ESTABLISHED，行動NOT_EVALUATED。main及所有原資料／策略／參數／舊圖保持。
