# 接續：候選起點已有可重現研究方法，正式終點未定

repo blue1998-glitch/Twstockai；分支dev/m1-v018-chart-annotations；本批起點02d16b504cb270bd001d0f8b2c4c2df42dfdb625。先核實際HEAD包含起點，保留所有後續成果，不使用main或舊ZIP覆蓋。最新研究／收據提交由本目錄GITHUB_READBACK.json及實際HEAD核定。

先讀AGENTS.md、CONTINUE_IN_WORK_MODE.md、M1_V019_GRAPH_CORE_RESUME_HANDOFF.md最新節及PROJECT_VISION.md，再讀本目錄README.md、summary.json、proposals.json、verification.json、manual-qa.json、WORK_LOG.md、GITHUB_READBACK.json。完整歷史限制沿../20261020_formation_features_work_review/WORK_HANDOFF.md及其前鏈，不再複製長全文。

本輪新方法為純研究函數propose(source,cutoff)，不接受目標起日／人工標籤／目標長度：反向掃描右側截止外包，舊K高／低擴張外包時保留該K與下一筆為候選。沒有改原M1的pivot／box／2高2低或3、6、12%參數。其他比較方法是新收盤轉折基準（平台須等右側不等完成收盤），以及所有日範圍共享正寬價位的最新最大短尾窗；它們都不是正式區間偵測器。

2884截至10/7：來源1207筆，原列缺日後保守可用段223筆；反向外包66候選，含9/17；收盤轉折111候選；共同價位只10/5至10/7的3筆。9/17只是原助手研究參照，使用者未核定它為正式起點；不能說命中正式區界。ABC截至6/2：可用139筆，外包25候選，含4/7與5/13；收盤67但不含5/13，因5/13最高影線31.40而收31.10低前收31.20。共同短尾窗5/28至6/2僅3筆，不能代替39筆原涵蓋。

4/7外包候選在5/14區內跳空後仍保留；不以每次跳空強制刪父觀察範圍。但截至6/3仍提出4/7至6/3共40筆，而使用者已確定6/3在原ABC前箱外。該提案只「觀察到當前」，formal_end／成員仍null，不能直接正式延長原區間。6/2的39筆研究提案與6/3的40筆各有獨立ID，固定輸出均保留；同起日不代表同正式結構／合併／承接。候選起點可生成，正式停止與成員規則尚未解決。

下一個具體目標：利用已有候選池，研究觀察範圍停止／保留／後續候選的可重現條件。以已知6/2在內、6/3在外的相鄰資料差異作驗收約束，同時保留6/2已創窗低仍在39筆、5/14內部跳空仍屬較大範圍；不能寫「創低即切」「跳空即切」。先自行分析可推導細節；只有真正新的重要核心含義歧義才附足夠廣角可放大實圖問，不再問已答案例或最早日。不要只反覆核同例數值或新增欄位就當辨識完成，也不能因已有候選來源就硬編正式區界／主壓力／交易資格。

所有方法限於原已列缺日後的保守研究可用段，較早歷史仍保留背景；這是來源疑點隔離，不是市場真正起點、不是舊帶降低重要性，也不表示完整日曆與公司行動已核。當時公開可得未核；本輪只是現在做的事後截止研究，不當過去實際選取。10/7無原核心／numeric_frame仍null，historical_selection_time=null、historical_signal_eligible=false、primary_pressure_id=null。新增收盤轉折為研究事件，不能冒充原引擎已確認轉折。加入新K時候選可變，但原截止輸出不覆寫。

本批proposal_research.py1次，5個截止；verify_proposals.py1次，五案獨立前向後段min/max、截斷與未來價格污染、正價格仿射變換、合成常數／平台邊界與362逐截止相等；不是分類準確率或市場樣本數。build_figures.py3次嘗試（首次拼字SyntaxError無PDF，後兩次成功），最終兩頁靜態PDF渲染實看及人工QA／預覽SHA綁定。沒有重算原核心MA/MACD/pivot/box/reaction、source-query adapter CLI、bootstrap、舊產品測試、瀏覽器Android，Android NOT_TESTED_NEW_BUILD；原三頁圖冊未重建。

重現先恢復原兩檔SHA（2884 ab87a51b...，1101 comparison184bdef...），路徑與來源恢復沿前批交接；不要抓新行情或覆寫舊數值：
python proposal_research.py --source 已核source-data-2884.json --comparison 已核comparison-data.json
python verify_proposals.py --source 已核source-data-2884.json --comparison 已核comparison-data.json
python build_figures.py --source 已核source-data-2884.json --comparison 已核comparison-data.json --font 可用CJK字型
只在有變更需驗證才重跑；新輸出需重新渲染實看，不能借用本批manual-qa收據冒稱新QA。

原已答2884完整上漲整理再漲、10/7足夠、ABC自己較弱區間、39筆4/7至6/2、5/13代表、6/3在外、1/27、11/25非關鍵點、小窗撤問、局部整體分判、異質整體、未挑戰舊高前不先降重要性全部保持；共享來源角色未答不代答。原相等不補過破、OHLC不推日內先後、來源可知／確認／後來選取分開、重複版本非獨立票、不同窗不排名，以及Raw公司行動／五年Adjusted／完整日曆／歷史公開可得／Darvas正文／SQLite限制沿原交接，兩股日曆分開。

分類NOT_VALIDATED、核心用途NOT_ESTABLISHED、行動NOT_EVALUATED。繼續Work；已定可重現規則或工程缺陷才交Codex。保留main、原核心參數策略庫歷史資料舊圖，不部署付費交易訊息子代理；file://不重試不繞過。完成同分支保存回讀，結束附已核提交、成品、完成未完成與可直接接續方式。
