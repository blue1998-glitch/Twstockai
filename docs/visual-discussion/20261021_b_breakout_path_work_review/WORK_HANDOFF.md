# Work續接：B小層至大層的價格路徑及三種量描述

儲存庫blue1998-glitch/Twstockai；分支dev/m1-v018-chart-annotations；本輪起點e57664243e662b82918c38a8877355a249ff3979。最新提交／回讀以本目錄GITHUB_READBACK_RECEIPT.json及實際HEAD核，不預填。main基線9c5b168c09ba80010c74f03b9c537e8b7474256a及全後續、原引擎策略參數來源圖不改。最高目標資金增值閉環＋正向資本成長飛輪不變。

先讀根AGENTS.md、CONTINUE_IN_WORK_MODE.md及M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節，再讀docs/visual-discussion/20261021_b_breakout_path_work_review/README.md、path-evidence.json、selected-events.json、cutoff-views.json、verification.json、source-provenance.json、figure-manifest.json、manual-qa.json、本檔與兩頁output/pdf/b-nested-price-volume-path.pdf。前輪20261021_b_nested_band_decision已答大小帶並存，小帶帶量跨過可能挑戰大帶、大帶價量突破可能有行情；不當必然或自動進場，不再問，A ABC G2亦不重問。

本輪沒有新增人工問題，只用B原價量研究實際跨層路徑。用4/16 H33.20與2/26 H35.50作原高參照，前者為較低活動／小層代理，後者為較大背景／大層代理，兩者仍非正式帶價界。不能把原4月任意微小段重新升成已核小帶，亦不能冒充已確定正式父子來源ID。原價可見與事後角色選取／歷史自動可選取不同，historical_signal_eligible=false。

June21筆的10截止視圖：6/3 H33.30 C33.00影線過收未過；6/4 C33.45上跨33.20；6/8 H33.10 C32.90整根回下；6/9 C34.20再跨，6/10 L33.15 C33.65／6/11 L33.05 C33.85低在下收仍上；6/17 C35.50只是等前高、6/18 H36.25 C35.40影線過收未過；6/22 C35.80收過35.50；6/24 C35.00回大參照下但仍小參照上；6/30 C34.45同狀態。6/9以後至6/30保存收盤都在33.20上。保留兩層各自狀態與反面路徑，不以一個break=true覆蓋，不把同過程重跨當獨立成功次數，不倒刪6/4當日事實或使用6月後行情。

成交量只做三種描述：對前一保存日、凍結3/16～5/29共52筆的中位量35,679,356股、此前20筆均量（不含當筆）。來源期事後選取非已核形成期，5/29完整以前中位量為null；前20筆為保存紀錄非日曆已認證。分子分母精確保留、展示兩位小數。6/4 V71,753,146雖低於前一筆，對來源／前20為2.01／1.47倍；6/9 V88,605,638為2.48／1.69；6/22 V106,058,238為2.97／1.66。6/5的1.38／0.98與6/23的1.58／0.84說明不同基準會有不同大小關係。三比較非三票或已選帶量門檻；volume_qualification全null，沒有自動正式突破／支撐反應或交易資格。

study.py2次、verify_study.py2次，第二輪修正相等出發與嚴格異側跨越混算：6/18是由等回下，不當曾在上後再跨下。最終10截止前綴／未來價量污染、9原價路徑、3當筆量翻倍但基準不變與比例翻倍、未完成中位量不可用、量比較分歧及原SHA通過。不是分類器或策略驗證。圖builder3、PDF渲染2，最終兩頁實看；初次成品後續結構核對發現不完整（原因未定），重建並改為主程式入口／暫存完成核EOF及頁數再替換，最後pypdf及pdfinfo核兩頁零影像物件，另核import不改成品。358筆一年半背景、167筆逾八個月價量細節，均至少六個月，同附PNG與向量放大PDF。

新量統計僅研究描述，原source指標不改；沒有原引擎／MACD／舊driver／舊verifier／產品測試、bootstrap、新行情、瀏覽器或Android。source-provenance保留原Raw公司行動／完整日曆／歷史公開可得與已列缺日／非窮盡資格，不能因無新已列缺日就稱完整日曆。圖中橙色短線標已列缺日，不補K。

分類NOT_VALIDATED、用途NOT_ESTABLISHED、新Android NOT_TESTED_NEW_BUILD、行動與飛輪成效NOT_EVALUATED；正式大小帶界／成員／父子來源／反應／量能資格皆null，使用者已確認層次關係不被改回未答。移機原source在docs/visual-discussion/20261020_independent_source_levels_work_review/source-data-2884.json，SHAab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901；可用STOCK_STUDY_2884及STOCK_STUDY_FONT重定位，不新抓或重算core補檔。

下一步維持Work，從已核兩層價格狀態及回收／再跨的當時價量，研究量的比較基準、跨過當日與續行／返回期間的角色，不先定倍數門檻、不把描述當支持已成立。不要重做相同過破查詢、不重問B大小帶或A ABC G2；真正重要新核心才附足夠圖問。判讀主圖至少六個月並擴展到看清大小範圍，同附圖片與放大版。例行多步、可逆修正及同分支GitHub交付已授權，不部署付費交易訊息子代理；若切換模式才附完整可複製交接。
