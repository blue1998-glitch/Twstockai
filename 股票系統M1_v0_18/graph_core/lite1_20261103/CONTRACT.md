# M-LITE1 顯示／載入契約0.1

## 保存真相

原core0.2、指標、行情與Journal均唯讀。新頁／分片版本獨立；新view-head不回寫current-increment-run或FM3 continuation。事件只使用原OBS1已投影的collection、candidate、pointer、事件日及first_observed_at；不新增過線算法。每股切片保存原source_index，建置逐股串回且與原事件陣列完整相等，429071／16954不丟棄。分頁是呈現，不是候選裁切。

## 判定是研究事實短句

僅當原stock/date/result/source/basis/prefix一致、參照已確認可比且未停止，投影截止日原過線事件。INITIAL不是突破；有原同日事件才寫突破／跌破／回區間等；無新事件只寫今日無新過線。多類並列為多參照分歧，不產生主參照或排名。數值等價的不同字串只合併顯示標籤，所有原字串／事件／ID仍在證據。價格線僅按原價軸定位；畫外不偽放軸內，來源圓點只綁真實原日期。多價位不暗選唯一價。

當日基底重啟／缺口、短史、缺行情與品質拒用直接明示不可判定／歷史不足；原停止比較不叫結構失效。量只沿原ratio_to_previous_means[1]對1精確比較，缺值不補0，不能把量增當已驗證配合、量少當壞或抹掉已過線事實。正式P0-3仍須原明示語義參照，本層不補它的角色；structural_invalidation與volume_confirms_price未知，formal_authorized=false、primary_pressure_id=null。

只讀所選批次完整截止前綴，未來候選確認不提前輸出，原晚選／公布可得限制不升格；UI不補算。原發生／確認／可觀察時間保留在次層技術明細。

## 最小載入與同源安全

啟動只有1986身分與短判定、日期及分頁路由，series與事件陣列均空。雷達每頁最多50股；每個展開證據包最多50原事件。股票數與事件數分開，日期按原首次可觀察日，不冒事件實際發生日。比較只限2～4股，重用同一comparisonScope，不評分。個股只讀所選原series；所有分片先核schema／identity／date／result／source／basis／prefix、原字串價格、SHA及長度。

所有請求經原owner驗證、same-origin、redirect:error、no-store、CSP。服務linked根必須顯式提供，只白名單preview/run/series-SHA.json與本新目錄的明示資料包；拒絕symlink、越界、任意路徑、身分／日期／描述衝突、SHA竄改及未認證訪問。未授權根頁不透露Location。換股載入期間離開頁籤須取消後續圖載入；錯誤不顯示上股舊圖。

## 容量與資格

新build原件根外獨立目錄；預先224MiB分片預算、32MiB工程餘量，寫入檢查至少512MiB空間；完成後含試作版本與驗證合計再核256MiB界內。不刪舊檔、來源根不增改；只實測新儲存增量，不把小HTML等同磁碟節省。同磁碟不當獨立備份。

來源0.10及全部parents不變，不新增catalog；execution_qualified=false、historical_signal_eligible=false、policy_authorized=false、imputed_close／valuation=null。Raw／五年Adjusted／公司行動／個人權利／主檔／SQLite未知仍在。無來源請求、無新核心／MA／MACD計算、無UI補價／量、無排程／外部部署／交易。Android NOT_TESTED_NEW_BUILD。
