# 可重用模組與欄位差異

基線為指定分支 `392b94a4f29b2e53fbfc0b7bda8a3fc1d0592b25`；確認1085b17及3b6fe93為祖先，並保留後續量峰讀回成果。初始tracked差異為空。bootstrap實跑0補缺、7個baseline差異保留；不是7個未提交檔案。此次只有原唯一Codex，無平行分支／子代理。

|實讀模組|現有可重用能力|本階段差異／處置|
|---|---|---|
|rotation_research/core.py|Decimal、明示成本、股數／現金研究回放|只重用fees；舊25%／50%、20筆高點代理與lag0不進新規則|
|rotation_research/loop.py|單一連續帳、舊10筆檢討實驗|不呼叫；舊固定檢討／漲幅選股非正式策略，不當新資金帳|
|rotation_research/store.py、CLI、action_cli|Journal不可覆寫、READ不重算、外部IO|新CLI直接沿用Journal，不遷移歷史schema；新增顯式EXECUTE及prior-id|
|rotation_research/action_ledger.py|權利、現金／股份應收、買進應付、已結現金、逐日帳、股利／配股／減資及缺價拒算|全部成交仍交此帳；不複製入帳程式。新adapter補委託預留、限價／狀態／容量、部分與未成交|
|action_sources／scope／resolution／後續來源資格層|原件、對象／日期角色／版本、精確parent及拒算鏈|不改producer或catalog；新增real_source_gate純委派介面，未跑真實新資格producer|
|正式action_resolution0.4|批准毛額／每人總額圓整，非每股淨額|不以假想股數補期初權利，不以新欄位解除FINAL_LEDGER拒算|
|來源0.10→0.9→0.8→0.7→0.6→0.5→0.4→0.3及原帳契約|來源角色與全部未解缺口|最新保存狀態核對仍70拒算／2不足／8換股影響未支援／總淨合格0。這是保存檔盤點，不是本輪重跑|
|structure_state/core.py／source.py|P0-3狀態、角色、支持／反面／缺證、完整事件及時序|新evidence adapter保存整個原輸出及false／null；不把轉強變上漲機率或新買進資格|
|reaction_facts/core.py|多參照三態、量／MACD描述、來源／基底／前綴|沿原來源綁定驗證；不以壓力價作保證目標，不補近期高點|
|manual_basis/core.py／store.py|已存在人工Raw／Adjusted精確選擇／持久保存|沿原validate_result；不新做模式路由，不默認退Raw|

|所需語義|舊能力缺口|新契約／界線|
|---|---|---|
|decision_at、data_cutoff、available_at|舊日日期不等歷史實際可知|新欄位皆帶時區，先過截止／可知篩選；數值與整檔metadata比較分開|
|來源、調整版本、參照角色|舊來源不同功能各有binding|mark／evidence／entry明確相同source/basis/adjustment；saved adapter核manual/frame/as_of；無正式參照保留null|
|可賣數、保留額、既有委託|原帳有持股／應付，無委託預留|新account逐欄顯式；多買單合算、賣單鎖股；未知欄拒絕，不補0|
|期初應付與既有待成交完整重播|舊帳無期初payable介面、無訂單生命週期|決策可行性可讀；simulate明確REFUSED，沒有假造成交或轉成現金|
|券商額度|原帳只已結現金|另有資格／版本／來源／可知時點／上限；只合成可行性，數值重播NOT_IMPLEMENTED|
|成交時間、部分／未成交|原帳只吃明示fill|新tape明示可知時點、限價／停牌／漲跌停、共用容量、交割日；不是逐筆市場模擬|
|單股／群組／帳戶風險、流動性|舊P1-7未實作正式組合上限|明示合成幣值與共同壓力情境／容量；沒有以停損假定最大損失|
|事件去重與後續檢討|舊固定批次不能證明新證據獨立|formation/event/volume柱共用token，resume承接已看token；不定固定比例／天數|
|公平權利|舊compare主要檢查初始NAV與期間|compare_jobs要求完整共同decision_input與ledger模板；同NAV不同權利也拒絕|
|建議與授權|不可由建議推資格|6個獨立欄位，全部外部資格仍false；F/R2明示未實作|

可重用不等已核來源／策略。新saved-layer adapter目前只做合成序列化及錯配驗證，未以新真實個股進行決策／成交重播；原P0-3、P0-4、Raw/Adjusted及量峰研究結果全部保留，未重算或升格。
