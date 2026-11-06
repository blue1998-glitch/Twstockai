# 原活單／未交割款跨輪續播0.1（事前契約）

本輪只續播已核准原單，無新決策、數量、批次、family或自動策略。新純入口`execution_continuation.resume_orders(request)`，input為capital-standing-order-resume-input/0.1，結果capital-standing-order-resume/0.1；觀察狀態capital-standing-observation/0.1。舊simulate、execution0.8/0.9及checkpoint0.7/0.8契約保持，不隱式遷移READ。僅擴充原execution的共享私有循環，使其接受**已重建驗證的執行狀態**，不是刪除原新決策的活單／應付拒絕。原ledger／成本／風險／fact規則不另寫。

## 輸入、來源與缺段

必要exact欄位：schema、synthetic=true、root_job、checkpoint、expected_checkpoint_id、expected_latest_decision_id、path、expected_path_id、segment_tape、observed_until、resume_at。root_job是原核准同一job的完整明示合成原件；全程原ledger／opening／orders／decision／close proof不變，root_job.tape等於完整path.observations。不能加單／改單／改policy或新增reassessment。已發生的重評／拒絕收據及全部token照原歷史帶入，尚待新重評的原單只能保持WAITING，不因備款到位自動放行。

path為capital-synthetic-order-path/0.1，必有fixture來源、原ledger ID、原資料起點、原窗口末端日終、完整觀察及逐交易日session_coverage。每交易日明示該合成模型的全部observation指紋及no_other_execution_opportunities=true，來源必存在於原合成ledger。空日必有明示無其他機會宣告；沒有宣告就UNKNOWN／拒絕，不能因空tape推定沒成交。此只是假想模型完整性，不是實際市場或來源認證。expected_path_id綁完整path，segment_tape必全文等於完整path在checkpoint之後、observed_until以前的全部觀察，不能漏掉中間點、重複、倒序或越界。

完整path／原件指紋為integrity，數值運算僅取截止前的觀察。未來價格／失效仍沿原available_at；未來metadata不同可改完整來源ID，但不能改早期可知數值狀態。resume_at不得早於checkpoint日終及其available_at，也不得越過第一個未處理觀察；不允許跳過中間成交可能性。窗口／日曆／報價只使用已保存明示合成原件，不添加1/13、不取新來源或真實市場。

## 驗證及真正承接

1. 原validate_checkpoint核原帳／fills／order狀態／fact／收據／tokens。expected latest及checkpoint精確匹配，原origin不可換。
2. 以root_job及完整路徑重建至checkpoint的前綴，只作歷史驗證和取得marks／risk_data／原單runtime，不是新帳或新成交。重建結果須全文等於原execution；舊單ID、價格、期限、已成交／剩餘與預留不能只信自報hash。缺歷史或屬另一條路徑即拒絕。
3. 真正續播從已驗runtime開始：保留fills／order states／history／events、decision records、latest、fact sources及reassessment_attempts；不呼叫新decide，不重置原單，不重新送單。共享原逐觀察循環只處理segment_tape，接受的fills再交原ledger核帳／交割一次。原始本金、其他資產／權利與一般reserve保持。
4. 內層execution.new_fill_ids仍是原job的累計範圍以維持舊schema，外層new_fill_ids_this_segment明列本次新成交。原fill ID由累計history長度接續，不重複入帳。到期／失效釋放只一次，已合法成交不因晚來公布撤銷。

輸出含原execution及完整新checkpoint、當次新fill IDs、歷史重建／尾段處理數、共享循環逐觀察audit，以及可比狀態。audit保留at、原單狀態／預留、已接受fills、marks、當時fact history／latest／token與引擎當時可用額；不冒券商盤中帳或自造另一套會計。比較以共同明示觀察點的狀態、全部原ledger逐日列及完整最終execution/checkpoint為準；不同完整來源ID與分段收據另列，不以終點NAV替代過程比較。

## 凍結合成案例與驗收

原窗口1/5～1/12。採既有cash_execution開現金B20 job；首段tape重用quantity保存的1/6 A/C/B7觀察，第二段重用已存1/9觀察，無新價格或日期。首checkpoint1/6日終：現金1000、B7、應付141.14、原單剩13／預留261.65039、一般reserve100，仍有現金80及C2股份權利。預期後續B13只再成交一次，費用與交割各按原ledger；1/8先結141.14，1/12結261.26並收原80，終點現金677.6、B20/C4，原本金1180保持。

另凍結尾段不成交／到期、已先到期原單不復活、較晚可知撤銷（保留已合法B7）、單純未交割而無活單、兩次續播及未知缺段等控制。每案例先存精確root/path/prefix/expected，再用未改原engine產生prefix/full控制actual；新實作後保存新續播actual及逐點等價證據，不改oracle。

必要反例：錯latest、改origin／orders、漏fill或order history、重複fill／觀察、漏segment觀察／日完整性、未知來源、越窗／時間錯位、未支援的新重評。必要未來隔離／完整Decimal Context／input不變與原已結清入口相容回歸；不跑整套舊suite。來源及原舊schema／結果／null／UNKNOWN均保持，基線execution.py另存指紋及差異，舊source版本以原件／baseline核，不要求新source仍等於舊manifest。

仍不支援：真實市場／外部任意委託匯入、沒有原job／完整觀察的帳戶、未知期初應付、限售解除、新決策／策略／批次、R2/F、來源認證及完整分叉。70/2/其中8/真實合格0、1101 UNKNOWN、正式false／主壓力null、來源0.10全部parents及圖形人工保持。無producer／新來源／UI／Android／樣本外／部署交易付費訊息，只唯一Codex原工作區／分支，正常保存及GitHub讀回。
