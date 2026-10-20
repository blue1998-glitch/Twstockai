本次新source／固定成品已核提交：`2d9c9aad4b88b53d9552e479a3f625377f2b7161`；逐檔GitHub回下載33檔／18,327,179 bytes、ZIP CRC／6成員SHA與抽出bytes PASS。回讀收據及本段另存後續文件提交，最新交接請實際讀分支HEAD。

請接續股票系統M1，同Work使用已完成的多參照反應事實附層研究整體壓力，不重做圖表／附層工程，不重問已答原則或案例。

儲存庫：blue1998-glitch/Twstockai
分支：dev/m1-v018-chart-annotations
本輪工程起點：c871eeb716b4d5a0206f1e00127b8d8ca719d54c
固定原真實圖：fff47915523fab8c8de8279de8bbb7a26b05647b
新source／成品與最新交接提交見本交付README末尾及GITHUB_READBACK.json；先取實際分支最新，核對包含上述節點及新成品提交、保留後續成果，不用main或舊ZIP覆蓋。不要把工程起點當最新成果；若無法讀GitHub要明說未取得。

依序讀AGENTS.md、CONTINUE_IN_WORK_MODE.md最上方、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節；全文讀deliveries/m1-v019-reaction-facts-20261020/README.md、本WORK_HANDOFF及GitHub回讀收據；股票系統M1_v0_18/reaction_facts/README.md、validation_20261020/驗收報告.md、examples/selection.json、generated/reaction-facts.json。沿讀docs/visual-discussion/20261020_reaction_facts_contract/內README、REACTION_FACTS_CONTRACT、CODEX_HANDOFF、facts及來源收據，及pressure_update_evidence/user-decision.json；原已讀案例與跨尺度圖契約保留，不重讀101圖、0.4.3或舊Android按鈕。

本輪新multi-reference-reaction-facts/0.1已實作：獨立純數值core.evaluate、既有cross-scale資料／selector來源adapter、CLI、完整精度JSON與資料小ZIP；沒有修改主圖或原core。先重用原number／fingerprint／ratio，舊trace_reference與volume_observation保留原義，不能把舊close-only相等命名當新三態。每參照close/high/low分別ABOVE／BELOW／EQUAL與精確差值，完整位置在records；transitions只索引分欄位變動／分段，49筆不是49個訊號或獨立型態。

來源為固定原資料1213根OHLCV／原MACD／SMA／source／basis／frame／prefix與原core／manual audit，不重新分析或計算指標。4個查詢來源以明示原ID／原K欄位解析：B77研究低界、5/14原高、B88研究高界、10/14原高。selected_at記本次後來實際查詢，historical_selection_time仍null；known_on只表示保存完成日／原確認日，不認證市場公布真實時刻，historical_signal_eligible=false。未到可知日NOT_AVAILABLE；後來選取不冒充歷史訊號。

body與前保存收盤分開、相鄰高低／Raw區間幾何非波段確認或正式跳空。量只作排除當日的前一保存記錄描述比，分子／分母／日期保留；商為50位有效數而非無限精確值。原MACD／null／reason與精確符號保留，不計算新MACD、不以正柱抹掉價格反證。缺價格斷相關路徑；已知待核日曆缺口保守分段，不證缺失交易日；basis中斷阻斷舊參照，不補假K、不跨缺口湊事件。日OHLC不推先高後低、次數、突破後回測完成。

實際準備：本環境bootstrap --hydrate-missing成功，0補檔／7既有差異保留。實際新22項Python契約測試PASS：九筆真實原值oracle、五月／十月完整路徑、多參照、相等／近零／長精度、前綴／追加改未來、未可知／延後可知、來源基底frame拒絕、缺漏零分母、MACD null、同價異源、既有helper等價、無策略／無修改、CLI／精確JSON／竄改拒絕及打包。最後22測試4.279秒。另實際原固定ZIP CRC／SHA與完整原來源／core全等、新ZIP CRC／6成員bytes及SHA、同分支GitHub逐檔回讀。不是舊7／47或35／60重跑；無UI改動，未跑新瀏覽器／觸控／Android。

交付fixture初次按同價＋同確認日映射得到各2個原候選，唯一性斷言停止、selection未寫而後續依賴FileNotFoundError；已保存診斷，改用原明示圖層B77／B88原ID，不任選、不合併同價來源、不調參。原2,155追蹤檔先核全不變，後來只增3份根交接最新節；原引擎參數策略、庫、歷史、舊頁、案例及證據不改。

請以新JSON及原真實互動圖對照以下已存反例，不把算術層當正式規則：5/14紅K卻較前收跌、原高低於前低；5/19收低於30.05而柱仍正，20／21又在其上但高仍低於30.50，22再下；10/12～16五位置／四轉換保留，10/13柱略增仍跌回；10/16高27.70>27.40但收27.30<27.40，低26.95相等不證回測。這些日期只作既有對照，不進生產策略常數。

下一步Work研究多參照局部證據如何支持、反駁或仍不足以判斷較大整體壓力。使用者已同意局部與整體分別判斷，不重問；不是彼此隔離，也不是較大壓力永不解除。不新增選關、正式解除、量權重、有效突破或買賣門檻。真正新核心歧義用具體真實圖討論，不逐根問卷；已定規則或可重現工程缺陷才回Codex。

primary_pressure_id=null；正式區界、量口徑／增量、強度衰減／重要性、合併／直接承接、生命階段仍未知。B77左拒6.05／3.5700／−2.4800、右拒3.25／2.4675／−0.7825不變；來源末轉折／確認／研究離箱／人工終點分開；89版本／84幾何組非獨立型態、廣義後來非直接承接、不等長觀察不排名。Raw公司行動／五年Adjusted／歷史公布可得／9待核日期與非窮盡日曆／Darvas正文／SQLite根因未知保持。核心NOT_ESTABLISHED、分類NOT_VALIDATED、行動NOT_EVALUATED；Android NOT_TESTED_NEW_BUILD，file://不重試不繞過。

保留原核心、參數、策略、庫、歷史、舊頁、來源案例證據與main；不部署、付費、交易、發訊息或啟動子代理。成果及實際研究證據保存同一指定分支並逐檔GitHub回讀；未讀未測未執行不得標完成。結束提供最新已核SHA、入口、完成／未完成及完整換模式續接指令。
