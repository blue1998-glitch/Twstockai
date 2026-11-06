# M2-3 FinMind 日線研究接線 0.1（實作前凍結）

只轉接 TaiwanStockPrice → graph-recognition-input/0.1 → 原 analyze；不改 core、設定或策略。純函式與檔案／HTTP 分離；不新增儲存框架。Free 限個人非商業研究，未取得行情散布權。

實例僅 2884、2026-03-01～07-22，分析 07-21／07-22。8069 只核庫內兩日官方整數張數的精度限制，不新查、不認證精確股數。純轉接限 2884/TWSE，合成 fixture 明標且不得用來替真實資料升資格。

JSON 用十進位字串／原數值字面值讀取，不經二進位 float；open/max/min/close 對應 open/high/low/close，Trading_Volume 原股數對應 volume_shares_scaled，絕不乘除1000。拒絕非法／重複／倒序／越界日期、缺欄、缺價、零價、矛盾 OHLC、非整數／缺量、錯來源／基底、未完成日、缺明示已知交易日及缺精確 as_of，不補值、不刪異常列。

expected_dates 為獨立保存官方同股月表的已觀察日期，驗證其原件 SHA；不是完整交易所曆認證。沒有可靠完整曆時 completeness=UNKNOWN，即使兩來源日期相符也不認證無缺日。日期比較與日線完成門檻以 Asia/Taipei（固定+08:00）解讀；同日查詢不推定收盤已完成，本版只接受 retrieval 的台北日期早於其後日之已過去日期。

historical_available_at 必為 UNKNOWN；retrieved_at 是現在取得時間，不寫進歷史 bar.available_at。這是依完整日線前綴的回看研究，不是歷史可交易資訊認證。只將 <=as_of 前綴送入核心；完整回應完整性與數值前綴分列，未來數值不得改過去結果。

2884 07-01 保存「不比價」警告，事件類型 UNKNOWN，透過既有 basis_break_dates 切開結構；不從警告推除權息、不認證跨基底連續結構。未核公司行動不靠無警告日推定不存在。primary_pressure_id=null、所有正式資格 false，UNKNOWN 與拒判保持。

完整回應、轉接 payload、graph 結果及可還原行情的衍生物只存儲存庫外的新本地目錄。CLI 拒絕 Git 工作樹內輸出；不覆寫任何既存檔案。不自動重抓；HTTP／API 拒絕不重試。公開驗收只用白名單的版本、時段、狀態、筆數、布林核對、缺證理由，不輸出行情／圖形價位／來源列或完整結果。

預期與合成輸入見 input.json／expected.json；先凍結再實作。原 core、來源原件與資金程式保持；不跑舊完整 suite／producer／市場績效，不重做 UI。
