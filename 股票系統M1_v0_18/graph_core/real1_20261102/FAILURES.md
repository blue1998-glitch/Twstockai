# 本輪失敗／修正與計數界線

1. 初次16方法有5個ERROR：重用的PORT1小型儲存fixture沒有真實FM3已有的stock.as_of。補齊合成封套，不更改產品截止檢查／真行情或核心。原log見tests-initial-failure.log。
2. 第二批有3個ERROR：合成HTML更新後，其current-increment-run及saved-batches仍綁舊SHA，被原清單驗證正確拒絕。同步新合成輸入的全部引用後，第三批16方法全PASS。見tests-fixture-binding-failure.log及tests-final.log；不是16＋16＋16個不同方法。
3. 同次自審把已完成build重送改為直接驗證並重用原收據／成品，避免wall_seconds不同導致immutable衝突；正例禁止再次呼叫projection。未放寬來源或日期oracle。
4. 第一個實體建置命令因環境沒有/usr/bin/time，尚未進入產品程式即停止；改直接執行同入口，只用實際wall_seconds，不安裝套件、不重抓來源。真正全批讀取只有一次，696.640秒，零核心／指標／供應者呼叫。
5. 幾個準備腳本第一次缺少repo的PYTHONPATH，或證據腳本把MA路徑寫錯為根模組；更正為既有src/moving_averages.py後完成指紋對照。這些不是產品測試PASS或市場樣本。
6. 真實瀏覽器首輪29組／8下載即全PASS，真實HTTP2,939成品逐bytes／SHA全PASS。沒有為圖形或市場結果改oracle。私人原圖與截圖不公開。

只有本輪最終16唯一Python、loader定向控制、原共用scope控制、29瀏覽器組與實際HTTP讀回是本輪實跑。歷史FM3／DU1／DU2／UX1／OBS1／COMP1數字不累加。Android、Oracle、外部入口、真實新交易日、永久備份及盈利均未因此驗收。
