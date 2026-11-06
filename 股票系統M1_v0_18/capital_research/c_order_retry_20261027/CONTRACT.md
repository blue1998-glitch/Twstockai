# C原單遭拒後再次重評0.1

基線3fb991255cdba69df97cdd677e5ea53c01122a8a。新增純API `conditional_retry.retry_rejected(request)`；只支援一份已保存review0.2的C原單遭拒結果，追加一次新的當期重評。不是新批次、不換family、不增量、不重開原帳；不接UI、來源認證或外部既有單。

## 明示輸入

`capital-conditional-retry-input/0.1`、synthetic=true，包含原始0.2 `original_input`、完整`previous_result`、精確`predecessor`、`review`與`observation`。predecessor綁完整原件ID、execution ID、checkpoint ID、latest decision/account及全部reviewed tokens。review只接受id／order_id／decision_template／policy，不能傳account／plans／targets／數量或family。模板與原欄位集合相同，政策edge／來源／可得時間明示。

只有`REPLAYED_REJECTED_REVIEW`且原單仍待重評、remaining>0、未取消／到期才可接續。原始0.2輸入委派既有完整quantity／重評閘門，重建結果須與previous_result完全一致；這是明示新RUN的來源鏈核對，不是READ重算或隱式遷移。原保存結果／source不覆寫，不承諾任意舊版本都可新RUN。

當期cutoff精確等於原保存watermark；decision在該日終及所有已收到attempt後。原帳由原checkpoint導出，不接受手填帳。原訂單及觸發／conditions／family保持，目標只能當期實股加原remaining，其他資產維持實股。全部舊accepted decisions、rejected attempts、facts、tokens及fills沿原帳保留；遭拒decision不當latest accepted decision。

## 原單回放接線

輸入只提供`observation.observed_until`及`tape_extension`，新觀察必須嚴格在原watermark之後、不超過原ledger窗口；原job／行情／calendar／clock／orders／歷史reassessments保持，追加一個新review。沒有在缺失區間推定無成交。若cutoff非原watermark、跨原日曆活單空檔、期初應付或無來源限售解除等既有能力不支援，明確拒絕／NOT_IMPLEMENTED。

新review ID不能冒用舊receipt。新decision仍沿原scope0.1、decision／execution0.9及checkpoint0.8，普通新批無同單豁免。有效舊事實可接受當期review，new_evidence_tokens仍空；新批仍需新獨立觸發。不能將成交／交割當批准。

若當期決策可行，但限制在較晚首次新觀察前已生效，本入口先明示NOT_IMPLEMENTED並保留新宣告及舊prefix，不能靠舊資格執行或把請求當已取消。這個窄入口不擴張原引擎的延後重評生效矩陣。當期已失效／撤銷／衝突的拒評仍沿既有attempt與限制機制保存。

## 輸出與READ

wrapper仍以review欄承載，明示schema=`capital-conditional-quantity-review/0.3`；新增retry_binding及previous_result_id。prefix是已核對原保存execution／checkpoint；execution_job／execution／checkpoint及numeric_result是本次實際接續，REPLAYED_ACCEPTED_REVIEW／REPLAYED_REJECTED_REVIEW分開。若新review尚未被引擎接收而原單先關閉，標`REPLAYED_RETRY_NOT_ACTIVATED`，不冒稱重評或成交。停止時保留原prefix和已生成的新request／decision，不回退成成功續抱。

純READ只增加0.3及新狀態的明示識別，不匯入數值引擎、不重建帳。原0.1／0.2的行為與保存bytes保持。所有正式資格false、primary_pressure_id=null、ranking=null。

## 事前驗收範圍

先存精確合成input／expected／source指紋，再實作與執行。沿已保存C UNKNOWN拒評原件；1/9日終核原帳，1/9 17:00再評，觀察至原1/12窗口。新觀察明示重用既存合成1/12 tail，不增加1/13行情。必要正反例包括恢復資格買原20、仍UNKNOWN、已撤銷／衝突、部分7或漲停0、錯前身／token／來源／cutoff／原單、額外數量或舊review ID、已關閉／已接受原件、延後限制不支援。核第一個拒評不消失、原權利／reserve／fills／latest與所有tokens完整，新批沿舊觸發仍拒絕。

不跑整套舊suite／九路徑／真實producer／資格重算／市場六方案／UI／Android／樣本外。1101期初cash_claims UNKNOWN／拒算、70／2／其中8／真實總淨合格0、來源及圖形／人工契約保持。R2/F、信用、期初應付、外部單完整重播等原未支援不擴張；Astra及救援原件未取得未讀。不部署、交易、付費或發訊息。只在原工作區／分支由原唯一Codex完成，依里程碑正常保存讀回。
