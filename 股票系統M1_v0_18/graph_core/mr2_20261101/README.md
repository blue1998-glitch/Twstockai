# M-R2｜來源前置核對 BLOCKED，未完成事件日簿

**本輪結論是BLOCKED，不是M-R2工程或驗收PASS。真實個股與同日雙市場成功接入數為0。**

## 可直接核讀的實際證據

- [來源與授權邊界](source-boundary.json)：官方條款、政府開放資料集、OpenAPI明示範圍及尚缺證明。
- [實際前置檢查](actual-preflight.json)與[執行log](preflight.log)：重用M2-3既存2884本地資料，經原graph_core0.2後保存BLOCKED。
- [事前輸入範圍](intake.json)、[事前預期](expected.json)、[保護指紋](baseline.json)。`diagnose.py`只物化本輪來源前置診斷，不是正式日簿producer／READ包裝或新引擎。

## 已實際做的部分

原工作區`/workspace/Twstockai`、原分支`dev/m1-v018-chart-annotations`，起始本地與遠端同`3d09ed82bcac303845e4d1b4ffdf37749ddd7dbd`且淨，未見其他活躍工程寫入者；這不保證平台外沒有寫入者，保存前另核遠端。沒有代理、worktree、新分支或第二工程。

重用既存FinMind2884有限回應及取得收據，核原SHA、原官方已觀察日期及07-01不比價警告；未新查FinMind、未改RAW／synthetic身分。原graph_core0.2實際執行：07-21供應97筆、當日新確認pivot為0；07-22供應98筆、新確認HIGH pivot為1，occurred_at=07-21、first_observed_at=confirmed_at=07-22。原ID／原始pivot及完整分析只留本地，沒有把7/22確認倒填為7/21已知訊號。

完整前置診斷沿既有`rotation_research.store.Journal`保存及讀回兩份紀錄，沒有第二套資料庫或改Journal schema／原帳。它們的status=BLOCKED、market_observation_date=null、markets_joined=false；**不能把已保存診斷稱為已接通雙市場的日簿。** source_contract_validated只證既有輸入／指紋檢查，不等來源全面認證、歷史可得或正式data_qualified。完整行情與可還原分析在Git外`/workspace/twstockai-local-data/mr2-20261101/journal/`，不進私人或公開GitHub。

2408未在本輪指定來源路徑／來源契約盤點找到可認證的原件；不推論整個倉庫絕對沒有相關提及。未新抓該股、未用合成替代。07-07警告及06-22／08-12人工參照只屬使用者提供的研究限制，本輪未取得原件驗證或升格新主要參照。

## 為何停止同日市場接線

實讀[TWSE條款](https://www.twse.com.tw/zh/terms/use.html)第06／08及[TPEx條款](https://www.tpex.org.tw/zh-tw/gtsm_disclaimer.html)第5／7：未經同意方式的自動下載受限制，政府開放資料另有例外。因此先核明示的開放入口，沒有直接請求網站歷史行情端點。

1. [TWSE開放資料集11555](https://data.gov.tw/dataset/11555)有政府開放授權，提供`MI_INDEX?response=open_data`。頁面機關2020-04-27回覆明示每次提供最新資料、不需日期；本輪讀到的2025更新詮釋資料仍未建立指定歷史日期與官方漲跌家數的入口範圍。這不是聲稱所有歷史資料均禁止使用，也不是斷言目前所有API都不支援歷史日期。
2. [TPEx開放資料集11369](https://data.gov.tw/dataset/11369)涵蓋收市指數／指數漲跌／漲跌家數，但未在本輪資料入口確認指定歷史日期的授權與回應綁定；[官方OpenAPI規格](https://www.tpex.org.tw/openapi/swagger.json)的實際名稱`/tpex_mainborad_highlight`沒有明示日期參數。沒有擅加參數試探、取最新資料冒同日或改用受限端點繞過。
3. 庫內既存`market-07.json`為加權指數月表，欄位「漲跌點數」是指數變動，**不是官方上漲／下跌家數**，不能充作市場廣度。Work M-R1報告／證據ZIP在Library，沒有可用正式讀取入口，仍未取得／未讀，不把摘要當原件。

本輪市場行情／OpenAPI行情請求0、歷史參數試探0、81日重抓0。文件及OpenAPI**規格**取得是來源核對，不是市場報價取得。沒有收到技術拒絕後換路重試或繞過；阻塞是本輪缺少符合日期及授權範圍的原始市場證據，不是證實所有合法來源都不存在。

## 未完成與未測

沒有實作或驗收：正式逐日事件日簿producer、同日雙市場成功接線、觀察窗未成熟／提前失守／完整窗失守等分類、完整來源／基底／時點／未來隔離矩陣。followup=UNKNOWN，觀察窗未設定；不填研究天數，不將未成熟當成功。不能因個股前置檢查成功冒稱這些機制通過。

新功能測試0、必要回歸0；沒有產品算法修改，所以不重跑舊18／12、81日、13敏感度或資金研究。SHA／來源／時點／Journal保存讀回等實際斷言只記前置診斷，不計成M-R2 PASS方法或市場樣本。沒有新增合成測例來掩蓋阻塞。

完整歷史普通股母體與歷史公布時間UNKNOWN；全市場成功率／失敗率、真實淨績效均null／拒算。原核心0.2／F-01、M-R1等待次數與參照、帳務／資金／正式策略未改；1101 UNKNOWN、來源parents與拒算、正式false／primary_pressure_id=null保持。沒有UI、回測、停買／減碼／恢復規則、部署、交易、付費或對外訊息。

## 下一個實際阻礙與交付

缺的是7/21、7/22**可核原件與合法使用範圍明確的同日雙市場官方漲跌家數及指數觀察**。不要求使用者下載／上傳或處理技術細節；也不為解除阻塞擴抓市場。若後續由研究端提供可正式讀取的既有證據或明示合適官方入口，再接原範圍；本輪不自行啟動下一項。

只保存程式未變證明、來源前置診斷與非行情摘要，正常提交／推送並固定SHA讀回。這是**BLOCKED診斷保存完成**，不是M-R2里程碑完成；本輪到此停止。人工操作：目前不需要。
