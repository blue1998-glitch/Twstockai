# 研究選擇紀錄純READ文字摘要0.1

基線521e0a168c0793859387dc1a0a378788d109d512。新增純函式research_choice_view.render_text(saved_choice)及既有research_choice_cli READ --format text；預設仍json，舊JSON envelope與退出碼不變。SELECT不接受text，不改舊選擇／驗證／Journal／帳務schema。

先沿read_choice讀回、校驗Journal身分及choice指紋與正式false，再渲染原件。一般／條件／拒絕意圖分開；顯示原理由、目標股數、保存資格／條件、截止／decision_at／recorded_at、來源／帳戶／checkpoint／latest指紋與歷史及當期reviewed token數。不把目標當持股／成交，不把當期reviewed token變已消耗token；完整ID仍在JSON。未保存來源綁定保持UNKNOWN，REFUSED無選中目標。

文字輸出是保存資訊投影，不重新選擇／計算或驗來源真偽；沒有完整來源與帳本，不新增現金／reserve／成交／行情或交易規則。來源時間與紀錄時間分開，WAIT只為等待交割後重評的研究條件意圖。渲染不修復缺失檔，不找較新來源、不遷移schema、不匯入或呼叫數值引擎、SELECT或Journal.save。輸入／庫內原件不變。

事前案例引用既有grid-intent、conditional-intent及rejected-old-trigger Journal，保存預期文字片段／退出碼；附錯Journal身分、choice指紋竄改、未知schema與缺檔的拒讀，及SELECT --format text在寫入前拒絕。只跑本次必要呈現／相容／副作用驗證，不重跑舊suite或任何producer。舊結果／oracle／log不改；本輪新actual與source指紋獨立保存。

70／2／其中8／真實總淨合格0、1101 UNKNOWN／拒算、正式資格false／主壓力null及原來源／圖形／帳務限制保持。無新來源、私人文件、bootstrap、UI／Android、樣本外、部署／交易／付費／訊息；原唯一Codex／原工作區／原分支依里程碑正常保存。
