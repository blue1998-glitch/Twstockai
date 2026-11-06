# 完整合成帳務評估0.1交付

## 實際完成

新增`account_metrics.py`純數值API及`account_metrics_read.py`明示source／evaluation_at的stdout-only外層入口。沿原`lifecycle.summarize_saved`校驗保存決策、原單、checkpoint、權利與token，不匯入execution／continuity／action_ledger引擎。原帳／策略／既有READ／schema與全部舊證據source未改。

從每輪累積ledger核共同原帳及日曲線前綴，只評估最後一份完整曲線一次；不拼接重疊輪次。保留完整account projection中的原資本、現金／應收應付、股份／待交權利、reserve、latest與全部token。此為保存結構及必要曲線檢查，不聲稱重新證明每筆分錄或來源真偽。

新增期間應計成長、每日回撤、最大回撤及峰／谷／恢復日期、最長峰值下方日曆日、尚未恢復截尾。每日曲線直接取成本已入帳的net_accrual_equity；與原帳期末假想退出後成長分列。退出成本沿原帳保存值，沒有第二套費用或帳務公式。回撤不是保證可成交的清倉價；pending權利仍在原應計曲線，不當可用現金。

## 凍結與實際驗證

先存CONTRACT、7份手算input／expected、16個source-bound精確recipe／expected及intake指紋，才實作production。每個recipe綁原件path／長度／SHA，解析後明示改寫由fixtures.resolve完整定義；結構反例重新簽章不冒原producer實際結果。另於自審後、補測前凍結2個mark錯配input／expected。既有oracle全部保留。

- 7份手算正例：恢復／未恢復／首次下跌／平盤／續漲／多段／平手新高。另5份未知／NaN／負淨值／缺日／重日反例。
- 18個保存結果或明示結構fixture：2份完整原件可評估、16份拒算；來源界線、缺值／缺價／缺日／原價錯配／交易日舊價、原帳前綴／資本／token、外流、可得時間、部分／停止／只有意圖有保存actual。
- 等價UTC與+08:00時區通過相同指標；早1秒拒算。3種fresh CLI設定（首批及補測共6個子程序）禁引擎import、帳務／回放、寫檔及網路；2種正常輸出及拒算JSON另存。
- 首次8唯一測試方法全部通過。自審發現原價內容與非交易日沿用需要明確校驗，補上純讀取核對及2個反例後，只補6個相依方法，全部通過。**本輪8唯一方法、14次方法執行**；未累加既有suite、案例或子程序。
- 改寫原資本案例預期拒算，實際被既有lifecycle的`ORIGIN_CAPITAL_CHANGED`先擋下；原預期較後方的`ORIGINAL_CAPITAL_CONFLICT`未觸及。保留原expected及diagnostics/earlier-capital-guard.json，沒有變更oracle。

兩份完整原件為partial-then-independent與wait-then-new-review：只解析其已保存結果，不執行原回放。前者原始2230、應計2225.640、退出後2216.530，fill費稅4只列一次；逐輪重疊日不重複計。實際部分成交／權利來源是舊保存原件，本輪不是新執行或新完整成交矩陣。

最終actual在`final/`、`cli-final/`及`time-final/`；`actual/`、`after-final/`與初批log為中途歷史。final/source-versions.json對目前production及原lifecycle；manifest不含自身。intake／preservation證明本輪引用的舊原件和引擎bytes保持，不冒全儲存庫或所有機制驗收。

## 未實作／未測／未取得

其他保存schema及精簡checkpoint、外部現金流績效、年化、來源認證、每日假想清倉曲線、現金拖累／大贏家歸因、同曝險對照、R2/F／原未支援帳務、完整分叉及自動衝突解除未擴張。僅有意圖沒有新成交路徑，不補1/13行情。

真實producer、資格重算、市場六方案、舊完整suite／九路徑、UI／Android／樣本外均未執行。70拒算／2不足／其中8換股影響未支援／真實總淨合格0仍為原保存狀態；1101期初cash_claims UNKNOWN／拒算不變。全部外部資格及授權false、主壓力null；不證策略有效或市場獲利。

Astra全文及第一工作區救援原件未取得／未讀，不猜測890檔存亡。Work未獨立讀本輪原件或驗收；本輪由原唯一Codex實作、自審與保存，無人工操作需求。沒有bootstrap、新來源、私人文件、部署、下單、付費或訊息。

## 下一項建議

可留Codex：把此評估接到既有明示合成回放的完成步驟，評估另存、READ只讀保存評估；停止或不完整結果仍拒算。不新增策略、行情、排名或自動選擇。本輪未進行此後續整合。
