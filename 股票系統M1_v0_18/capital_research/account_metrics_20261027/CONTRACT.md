# 完整合成帳務的全帳戶評估0.1

最低基線4313799a78d3d319a12da83ad8a0f661126c54cd。新增純數值account_metrics與stdout-only外層入口；不重播或重建帳、不補行情、不選策略、不排名。舊trend_replay及全部保存結果READ不重算、不遷移；不是把舊九路徑重新驗收。

## 明示輸入及支持邊界

capital-account-metrics-input/0.1固定schema、synthetic=true、evaluation_at（有時區）、saved_result。第一版只接完整capital-quantity-replay/0.1的COMPLETED_PROVIDED_ROUNDS，各輪須有完整execution/checkpoint。沿lifecycle.summarize_saved校驗原決策、權利、原單、latest與tokens，再核完整checkpoint原件／原帳／外生資產來源皆為ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET。synthetic標籤及自洽SHA不是來源認證，不接受改標真實來源來繞過拒算。

觀察截止不超過evaluation_at，最後close.available_at亦須已到；沿原來源calendar每個日曆日恰一筆，不排序、不補缺日。每輪累積ledger.daily必與最後曲線相同前綴；只用最後一份原帳完整曲線一次，不加總重疊輪次或費用。原始資本／opening不變，external_flow必明示0；外部流入流出、其他結果schema及無完整checkpoint能力仍未支援。中途停止結果不可冒稱完整期末結果。

原ledger須為QUALIFIED_ACCOUNTING_SCENARIO_NOT_STRATEGY_VALIDATION且無拒算／quote_gaps，opening_claims/net_distributions/calendar仍沿原明示合成資格。任何缺值／非有限值／缺價／未知權利／非正淨值／日期缺口都拒算；不補零、補價或從端點插值。保留原現金、應收、應付、股份／待交權利、一般與原單reserve、完整latest及token。只檢查保存結構與必要數值一致性，不聲稱重新認證每筆會計分錄。

## 數值口徑

- 曲線直接取原daily.net_accrual_equity：已反映實際保存fills成本及已知應收應付／股份權利；**不是每日假想清倉價**，不保證當日可賣。曲線不再扣fill費用、不扣reserve或應付第二次。
- 期間應計成長=最後原帳應計淨值/原始資本−1；幾何連結日變動等同此比值。不是年化、不是單筆報酬除天數。
- 期末退出成本、end_net_equity及scenario_net_return直接保留原帳值並核相互一致；另列期末成本後成長。不把它當實際已清倉或真實總淨績效。不另算終端成本公式。
- 每日回撤=當日應計淨值/截至當日最高應計淨值−1；最大回撤取最負值。相同最深值保留首次，平手新高在開始下一回撤前取最近日期。
- 恢復是回到先前峰值（大於或等於）；每段保存峰日、首次低於峰值日、谷日、恢復日。duration是峰日至恢復日的日曆日；未恢復以最後觀察日截尾且recovery_date=null，不把截尾天數當完整恢復時間。無回撤時最大持續日0、episode=null。包含非交易日原帳觀察，不補市場bar。
- mean cash weight不冒現金拖累，事後winner、曝險配對、年化／風險調整報酬、策略優劣均不計算。ranking及selected_strategy=null；正式資格false、primary_pressure_id=null。

## 證據與驗收

先凍結本契約、精確合成曲線／expected、保存原件path/bytes/SHA及明示改寫recipe，才實作。手算曲線只是數學fixture，不冒稱新市場或新帳務producer actual。保存原件案例只由明示檔案解析／結構校驗及數值評估，執行與帳務引擎呼叫0；實際結果另存actual。

正例含完整逐輪原件、手算成長／回撤／恢復／未恢復／平手與多段、原費用只計一次、已知權利原樣保持。反例含缺值／缺價／缺日／非正淨值、部分或停止結果、錯前身／token／原資本、超前可得時間／外部流量、真實來源及只有意圖。必要純函式與fresh-process禁引擎／寫檔／網路驗證即可，不跑舊suite／producer或九路徑。

1101期初cash_claims UNKNOWN與70／2／其中8／真實總淨合格0、全部來源parents／圖形／人工基底及未支援帳務不變。R2/F、來源認證、策略閾值、完整分叉／新行情／樣本外不擴張。不bootstrap/hydrate、不部署、交易、付費或訊息；原唯一Codex依里程碑保存自審及正常commit/push固定SHA讀回。
