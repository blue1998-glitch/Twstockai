# 本輪失敗與修正留史

以下不是累加測試成果；原私人stdout／stderr、各版HTML、目錄與PNG全留Git外，不改舊頁／原件。

- 首次render使用不存在style.css；核原檔後改重用viewer.css。相同UI再render寫含新時間之不可變收據產生衝突；改先核已有HTML指紋並重用原收據，不覆寫它。
- 首次服務4秒readiness太短，回報失敗但已啟同一服務；先核PID及port，沒有再啟競爭writer，之後只將自己臨時只讀server換成同8765之head模式。不是Cloud修復或SIGKILL根因結論。
- 第一輪瀏覽器查詢控制收折，測試沒先點「價量查詢」而timeout；修正測試操作，未硬開技術欄位。
- 第二輪由雷達開箱自動展開舊長證據抽屜，確實擋住底部雷達按鈕；改點候選先定位原圖及短判定，長證據留明示展開。真實重測通過。
- 舊批次測試用相同HTML basename找路由，誤取11/02；改用原目錄entry SHA＋檔名精確選10/30，保存錯誤與前後證據，未改來源或日期oracle。
- 邊界腳本fixture只有identity／code，誤用不存在market找TPEx；改核identity前綴，仍保留2～4股及上櫃原值控制。
- 最後來源驗證腳本本機變數http遮蔽http模組；修正變數後再跑同一來源／HTTP閉包控制，保留首次stderr。不記成新產品缺陷或額外測試數。
- 有一次本工作測試持鎖時嘗試寫新benchmark腳本，治理gate拒絕ENGINEERING_WRITER_BUSY；等本測試結束才寫，沒有刪鎖、繞過或啟另一writer。
- 額外低風險控制：切換分頁會取消尚在等待的個股載入，延遲真實保存資料之瀏覽器控制證明不跳回圖、不接著抓完整圖；未改數值或新增行情。
- 手機截圖發現圖上短判定背景遮到右側最上方刻度文字；背景只畫至K繪圖右界，價格軸原值保持，最後三尺寸圖重測。

原M-DAY1首次SIGKILL原因UNKNOWN、舊xref／Fontconfig／SQLite／file://歷史及所有受拒入口不變。本輪未重抓、重畫其原件，也未重試受拒入口。
