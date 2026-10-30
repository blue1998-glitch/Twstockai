# 本輪實際結果與剩餘阻礙

起點50d8c5e36285a2c3cd107a9a7a0dd7596c22b2ea，指定dev/m1-v018-chart-annotations；已核遠端與本地相同，fetch／ff-only及祖先檢查成功。沒有後續成果被覆寫。main仍9c5b168c09ba80010c74f03b9c537e8b7474256a。

本環境重新執行bootstrap --hydrate-missing成功：0補缺、7差異保留、baseline_verified=true、current_tree_matches_baseline=false。標準Python，無新套件、常駐服務或UI。

## 已取得的官方來源

25份成功原件、1失敗，完整清單source-manifest.json。16份是2025/07～2026/10的FMTQIK市場成交月報，其餘是官方首頁／導覽／報表程式、減資預告及申報頁與兩個成功回應。依官方導覽連結、表單data-api及腳本確認新資源路徑，沒有重試已禁的權息端點。

月報日期列在本輪窗口內317個，與1101及2884既存317日期全相符，無缺保存日期或多出市場外日期。逐日473行保存，來源SHA／URL／UTC／列欄定位齊全；後來擷取不能認證原當日已公布。月報中的10/16後資料不倒灌。以原計畫假日交叉核對，無「計畫休市但市場報告開市」衝突；2026/7/10為額外無交易工作日，與既存個別臨休證據方向一致，但本輪直接依官方市場月報，沒有重跑舊休市驗收。

1101 2025/8/13、2884 2025/11/5在市場日清單內，原個股無報價仍null，原因未知，不能當市場休市或認證停牌。未變動原OHLCV、Raw基底、來源識別／量、日線指標或任何舊分析。

減資TWTAVU當前預告只有一筆他股未來事件；sharesChange有209筆申報程序、1101／2884無命中。這兩表都不足證明研究期無其他事件，沒有新增被核實的1101／2884公司行動。歷史TWTAUU使用官方表單所列日期參數查2025/7/1～2026/10/16，得到HTTP307 Temporary Redirect；失敗meta保存、不當空表、未重試或猜其他端點。

## 實際執行及通過

- 新15定向unittest全通過，完整名稱／log保存。涵蓋真實317日期、原null仍開市、每行來源定位、缺月／錯月／錯誤統計、未完成擷取、未來資料隔離、越界／指紋、拒算條件、零命中非無事件、失敗capture不重試。
- 離線producer實際重核122份舊價量原件與meta；舊input／manifest仍與原reader產生內容完全相同。
- 70原研究窗逐一接新官方交易日，再實際呼叫原action_ledger，全部仍REFUSED，但不再有日曆未核原因；2個40筆不足仍不足，總淨報酬合格0。未重用舊無股利成交、未執行新策略比較或選比例。
- 原action帳44測試與P1-7的18／9982／Chrome36皆未在本輪重跑，不當新測試數字。沒有UI變動／瀏覽器／Android，本輪0次，Android仍NOT_TESTED_NEW_BUILD。
- 本輪小包會另以新目錄解壓，執行同15測試及producer後核對manifest；結果在根deliveries/m1-source-qualification-20261022/PACKAGE_VALIDATION.json，不把兩次15算30獨立測試。

## 未完成與設定草稿

完整減資／其他公司行動、2026/7/25～10/16權息覆蓋、2884當期配股比／可交易日／零股、淨分配／稅費情境與期初權利來源仍缺。entitlement-requirements.json逐欄保持null，不將公司基準日當除權息交易日，不假定無事件或稅費為零。原Raw公司行動／五年Adjusted、歷史公布可得、普通股主檔及SQLite根因未知保持；正式結構／主壓力／合併／生命階段／全換分批比例與策略資格未變。

上一輪玉山官方2025會議紀錄PDF因Tunnel403未取得；本輪沒有在相同限制下重試。官方減資說明另指向mops.twse.com.tw的原始即時公告，該host未列於目前自訂網域，尚未請求。

已按cloud-environment-onboarding:setup保存設定草稿：保留TWSE／TPEx與preset，新增www.esunbank.com、mops.twse.com.tw，更新start_skill為最新來源／會計接續；既有install_script／repository掛載設定／secrets未改。工具status=saved、requires_publish=true，**未套用當前runtime、未代為發布環境，兩新域尚未驗可讀**。具體目標URL、舊錯誤路徑與草稿收據在configuration-review.json。

必要外部動作是在產品環境設定檢閱並按其流程套用草稿，再用Codex核對runtime及受影響的單一請求；不承諾放行後一定拿到完整欄位，也不能因此重試被明禁的舊權息端點。技能明示「Saving persists configuration; it does not execute scripts, apply runtime changes, or publish.」此設定限制不是策略裁決，無需使用者猜門檻或比例。

原引擎／策略／庫／歷史結果／舊頁／舊ZIP與前輪事件帳檔案不變；根與rotation交接僅前加新節，保存核對見preservation-audit.json。未部署、付費、交易、發訊息或啟動子代理。
