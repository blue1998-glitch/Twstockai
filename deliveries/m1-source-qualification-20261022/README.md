# M1 官方來源資格補充 0.1（本輪入口）

**已補核指定TWSE資料窗的市場交易日；真正總淨報酬比較仍0合格。**

[下載新小ZIP（約0.67 MB）](https://github.com/blue1998-glitch/Twstockai/raw/refs/heads/dev/m1-v018-chart-annotations/deliveries/m1-source-qualification-20261022/m1-source-qualification-v01-20261022.zip) · [SHA256SUMS](SHA256SUMS) · [封包收據](bundle-receipt.json) · [固定提交及逐檔GitHub回讀](GITHUB_READBACK.md)

SHA256：`2411f934b290edd3f65cb30b5ebb3b20c9aba9fb5099e454fd5a57e335652542`；671142 bytes，375 members。原事件帳ZIP完整保留；新包內也逐位元保留原293成員，另加本輪來源與驗收。

[完整來源／驗收／缺口入口](../../股票系統M1_v0_18/rotation_research/source_qualification_20261022/README.md) · [可直接貼回Work的完整指令](../../股票系統M1_v0_18/rotation_research/source_qualification_20261022/WORK_HANDOFF.md)

- 16官方市場月報，2025/7/1～2026/10/16的317交易日期／473曆日，與兩股保存日全符；122原價量原件重核，未補行情。
- 1101 2025/8/13、2884 2025/11/5：市場開市但個股原null，原因未知，未補價或猜停牌。
- 新15來源測試通過。新資料夾解壓後同15項再通過、producer成功、374 manifest成員重現後仍bytes相同，CSV473行／317市場日／兩null核對通過；不是30個獨立測試。[實際封包驗收](PACKAGE_VALIDATION.json)、[測試log](package-tests.log)、[producer log](package-run.log)。
- 70窗僅日曆條件解除，仍因完整公司行動／淨分配／期初權利全部拒算；2個40筆不足。減資歷史HTTP307保留，當前預告與申報表零命中不證明無事件。2884配股比／可交易日／零股及7/25後權息覆蓋仍缺。

解壓到新資料夾先讀根README.md。本包含可離線驗證的必要原件與Python，不是整個歷史專案；前輪START_HERE及44測試屬原事件帳，不當本輪重跑。沒有新UI／瀏覽器／Android，Android仍NOT_TESTED_NEW_BUILD；原策略、引擎、庫、歷史、舊頁及main保持。

下一步用**Codex**。已有網路設定草稿供使用者在環境設定套用：保留TWSE／TPEx及presets，新增www.esunbank.com、mops.twse.com.tw並更新start_skill；工具requires_publish=true，未代為發布環境／部署，也未驗新域可讀。前者補玉山會議紀錄，後者查原始公司行動公告；目前只有已存PDF403及未列允許的MOPS來源需求，不反覆請求。套用後先核對runtime及個別來源，取得原件才更新資格。淨分配可採有來源且情境明示的稅費模型或實際證明，不能默認無稅／無期初權利。

格式檢查首次指出官方HTML原件自帶尾端空白；保留原件bytes與SHA，未清理或重寫。程式、交接、JSON與CSV的git diff --check通過；僅原件raw/*.response不套用自行撰寫檔案的空白規則。
