# 實際執行與修正

起點bbc85a7f5b6c587ae97bbd7c185d71b3f6ba5654；同分支dev/m1-v018-chart-annotations。已核遠端HEAD，讀指定三根入口最新節、前批完整WORK_HANDOFF與既有方法；本批檔名日期沿前批20261021，不以主機時間補造歷史事件。

1. 先讀既存633分支池及G2外部範圍事件，唯讀查看來源後續。發現G2整根離開後2/22接觸、3/1收回，ABC至6/13九筆仍整根在下。這是後來可得的差異，不用作較早判定。
2. 新followup_research.py driver實際1次，讀原事件另建persistent monitor、seed收盤轉向與價位歸組。633追蹤、119池內群組，八指定截止；未重跑上兩批driver，不改原函數或輸出。來源與原池SHA核同，沒有新行情。
3. verify_followups.py實際1次通過：28143逐筆幾何、633追蹤與成員來源、119群組、21去重事件逐截止、八截點未來污染與正仿射價關係、合成相等／對側／遇列缺日停追／未到事件日拒絕。收盤轉向用不同的價位平台壓縮方式獨立比對。這些檢查不是產品分類器、舊驗收或市場樣本。
4. 新build_figures.py成功2次。首稿兩頁完成及渲染實看，第二頁箭頭文字碰到面板標題，已降低標註位置後重繪兩頁，再渲染逐頁實看。第一頁內容不變，最終兩頁無文字重疊或裁切。原歷史圖冊重建0次。本批未出現前批截斷PNG問題，不把前批錯誤冒算成本批。
5. 最終PDF147825 bytes，SHA256 9f7143623a74ff47e6727c71d44dc38bfa1e756ca0bb4a144f28a79975fda7d3；PNG用PIL檢查、複製fsync並逐bytes回讀，manual-qa.json綁定最終檔案。靜態研究圖檢查不等於Android或瀏覽器驗收。
6. 追加新根入口與完整接續，不覆蓋任何舊文字。保存原分支、固定提交逐檔回讀，另存GITHUB_READBACK.json；實際提交與成功以收據和最終HEAD為準。

無核心MA/MACD/pivot/box/reaction重算、adapter/source-query CLI、bootstrap、舊14/22/60等產品測試、前批362／208測試重跑、新瀏覽器或Android。無子代理、部署、付費、交易、訊息。未改main、核心參數策略、舊資料與舊圖。正式選擇未定；分類NOT_VALIDATED、用途NOT_ESTABLISHED、行動NOT_EVALUATED、Android NOT_TESTED_NEW_BUILD。
