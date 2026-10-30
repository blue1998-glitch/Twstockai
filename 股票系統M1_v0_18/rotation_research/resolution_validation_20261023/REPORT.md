# 本輪保存後續成果及環境驗收

使用者起點d11cd18a，已實際重新bootstrap成功（0補缺／7差異保留）。作業期間完成了一份本地平行草稿；提交前CAS父節點核對發現遠端已前進dae1f6e，檢查在stage／commit前停止，沒有覆蓋遠端。

讀完新的action_resolution_20261023完整交接、契約、原碼與證據後，確認其0.4已涵蓋本輪正式決議及每人總額圓整要求。故將平行草稿完整另存於本地/workspace/m1-final-cash-v04-20261023/local-draft，不發布重複功能；還原的六份入口均為本輪自己的暫時前綴，先備份再fast-forward採用遠端，原使用者差異／四組未追蹤歷史保持。

採用的正式0.4：action_resolution及source producer，嵌入不改的parent0.3／五組件；新增批准決議與兩庫藏股分次報告。普通股每人總額先算再捨去，明示假想權利股數才有毛額。批准階段不是調整後最後分配、稅務細項或個人淨到款；沒有每日numeric replay路徑。庫藏股銷除不是股東減資帳。未改其金融原碼／契約／catalog或舊封包。

採用最新程式後在本環境再次bootstrap成功（0補缺／7差異保留），紀錄bootstrap.log。新增test_resolution_validation兩項：不同人分開圓整，以及PDF工具版本下所用頁／欄位保持相同。原0.4的29測試與新增2項，在本環境合計31項通過，見tests.log；沒有把前代24／17／44／15或18／9982／Chrome36當本輪重跑。平行草稿26測試只是未發布草稿紀錄，正式本輪採用的結果是31項。

## PDF抽字的實際失敗與界線

附加重抽用pdftotext25.03.0，原Work24.02.0。首次整份文字byte equality assertion失敗，舊54,910bytes、新54,843bytes，首個失敗、兩份SHA、原PDF SHA與完整diff皆保留。差異在附錄兩處斷行／重複逗號。原件與舊文字未改；用到的第1／3／4／6／7頁逐位元相同，正式producer的所有解析欄位精確相同。新增測試對正式producer再核，不放寬數值容差，也不把此結果稱全文byte equal或完整行動覆蓋。

## 重現與GitHub

正式成品dae1f6e的28變更檔已逐一從固定GitHub raw讀回，HTTP200、位元及SHA全同，見canonical-product-readback.json。本輪新驗收包會在新目錄執行31測試與正式producer、校驗所有舊新manifest及原511包成員；實際結果只以delivery/package-verification與extracted紀錄為準。原成品、庫及歷史不在工作目錄重算覆寫。

原0.4資格結果維持70拒算、2不足、8換股影響未支援、真正總淨報酬合格0。新解壓producer的實際重現數字另見delivery，不把僅讀舊輸出冒充新計算。每日淨帳／六方案／排名未跑，毛額不是個人績效；本輪沒有新官方網路、UI、瀏覽器或Android驗收。

仍缺完整公司行動／減資及2026/7/25後權息、2884未圓整／可賣日／零股及換股影響、台泥最後調整分配／直接有效稅務細項、個人淨分配／實際到款與期初權利。所有MOPS／TWT49U/TWT48U／TWTAUU／file://／NHI403及公報PDF403均未重試繞過。兩缺價日原因UNKNOWN、不補價；Raw／五年Adjusted／歷史公布／主檔／SQLite未知保持，無自動交易或新策略。

保存核對輔助命令初次誤用專案子目錄為根，找不到.gitignore而未執行雜湊核對；改用絕對根路徑後全部原追蹤檔一致。先行產生的未發布封包移至本地暫存，最後才重建含完整保存證據的成品；見verification-command-diagnostic.json。來源與正式程式未改。
