# M-CAP1 補正0.2｜完整合成帳戶清算

## 新帳戶，舊權利不被消除

原0.1的三支、HTML、ZIP、JSON、PNG、收據與所有歷史不改。原1/8帳戶C2已持有，另C2於1/9交付、1/12才可交易；現金權利80亦1/12收。原C4即時退出仍被舊cash_action以SELL_QUANTITY_EXCEEDS_AVAILABLE_SHARES拒絕；本補正多股門禁也因待交付股權拒絕。見original-refusal-summary及完整原輸入／回應；沒有原帳戶全清算績效，metrics=null。

新例僅是明示條件的另一個ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET帳戶：期初現金1000、B7／C4均已可賣、A0、無應收／應付／待交付權利或外部既有單，一般預留100。期初淨值1240，不能與舊1180本金混比，不認定原C股已獲解除。新declaration-v03是合成時點宣告第三稿，不是正式策略／來源版本。

四支同一1/5～1/12八日、同種子checkpoint及原帳戶權利、相同資訊／來源／RAW基底／政策／成本／風險與執行模型／觀察tape。沿原保存日終時鐘：1/5 14:00開期，先HOLD至1/6 16:00形成完整checkpoint，1/6 17:00明示四方案，1/7觀察成交、1/9明示交割；不是推造真實市場收盤或T+2規則。完整前綴及本金不重設。

## 最小接線，原財務引擎不改

續抱、減碼B3、退出B7保留C4仍用cash_action＋cash_action_execution＋action_account_metrics。原cash_action只核單一股票賣出；新basket.py只補明示多股全退出範圍／訂單綁定，不改舊schema或來源0.10。

全退出先重用舊單股退出核准資訊與_account_binding，要求完整held/sellable相等、全部持股及精確股數有明示sales、無待交付股權／未知權利或未完成外部交易；繼承原tokens／一般預留。以原family E／R1明示全0 targets再由原resume_decision核可行性。每股SELL委託的總量必須精確涵蓋所有原持股，不生成委託、不選比例、不容買入／額外／漏股。

執行沿原_job來源／日終／時點檢查構成多股外部job，再用原simulate與make_checkpoint。手續費、稅、滑價、現金／權利、交割與日帳完全由舊引擎計算。全退出收據用新cap1-explicit-full-exit版本，沒有偽裝舊單股或quantity-replay producer。

READ沿原_pair、_chain、_account、source_snapshot與完整指紋／來源／原ledger／clock／訂單／事實史／checkpoint檢查，之後只調原account_metrics._evaluate_snapshots。READ不呼叫evaluate／resume／simulate，也不重建財務曲線。這是合成保存綁定驗證，不是獨立認證真實券商或每一原件。

新compare重用舊basis，逐支完整資訊相等、截止前帳戶前綴相等。任一分支不完整、混帳戶／模型／期間／來源就整組拒比；renderer也要求宣告與比較的原ledger／時鐘／資訊／policy／tape／截止精確一致。全精度原結果直接呈現，不以原候選或單筆報酬取代整個帳戶。

## 全現金判定

只有全部股份0、現金及權利欄完整且有限、未交割應收／應付0、現金及股票權利清單空、已交割現金等於帳戶淨值、所有訂單終結且無預留、每筆SELL都有唯一明示交割入帳、來源日曆／期初權利／淨分配資格均滿足原合成資格時，終態才是VERIFIED_ALL_CASH_SYNTHETIC。

日圖只從保存日終顯示「仍有持股」「已賣出待交割」「已全現金（已交割）」。不推造盤中順序或即時可用現金，不將終點守恆當所有中途正確的唯一證明。真實執行反例另外跑部分成交B只3股，和截在1/8尚未交割；兩者都不得升格全現金。一般預留100保留，不等100%可自由再投入；過去未定解除模型仍未實作。

淨值／報酬已含已發生費稅與原成交價中的滑價，假設清倉與實付不混。正式total_net_return及actual_realized_investor_return仍null；這些是明示成本模型下的合成績效。零只限有原值；未知不補0。無回撤的續抱明寫本期未發生回撤，不假稱曾回復。

原核心、正式策略、資格、引擎、庫、FM3、來源0.10／所有parents、P0-3／P0-4、歷史Raw／UNKNOWN及警告不改。execution_qualified／historical_signal_eligible／policy_authorized=false；primary_pressure_id／imputed_close／valuation=null；不排名、不給真實交易比例、不部署／排程／交易。
