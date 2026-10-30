# 本輪實際執行／修正紀錄

1. 接續4c8d483，讀最新根指令與交接、既有產品來源說明，全文重讀PROJECT_VISION以最新保存收盤為錨。改用2884原凍結資料核來源層級，未向使用者索答遠端舊箱分段。
2. 原GitHub大HTML路徑初用整串百分比編碼把斜線也編碼，API HTTP400；改為各路徑元件編碼後下載成功。不是產品缺陷。
3. 原HTML SHA與解包指紋、獨立core blob及內嵌物件等值通過。探索輸出曾對int rejected_geometry_runs用len、對list reference_candidates用keys，分別TypeError／AttributeError；按實際型別修正。reference_candidates原63筆，不能說原來源總數0。未因此重跑產品。
4. 執行audit.py成功；只讀核對1213筆、15預存截點、34原箱、原極值／轉折資格及同尺度前綴後綴共點。不匯入引擎、不重新擷取行情或計算指標。
5. 新建三頁PDF及兩原尺寸PNG。首稿日期尾端重疊已改稀疏；補可見39.10／47.35來源標示。首批第三頁PNG不完整，PIL與view_image拒讀；不當作通過，重新完整渲染與檢查後再登錄QA。原因僅觀察到輸出不完整，未認證底層成因。
6. 最終逐頁渲染／放大／文字檢查、GitHub逐檔回讀與範圍核對見verification及GITHUB_READBACK實際紀錄。原14、22與60等驗收均未本輪重跑；沒有ZIP、瀏覽器、Android。
