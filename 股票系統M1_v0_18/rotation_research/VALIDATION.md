# 本輪實際驗收

bootstrap HYDRATED_PRESERVING_CHANGES：545補缺／7差異保留／baseline_verified=true。首呼叫早於sparse checkout完成而無腳本，完成後成功，未改指紋。18定向unittest PASS，9982來源／資金／前綴斷言PASS。122原件SHA與Git原件全等，420方案完整現金與股數守恆；4真資料前綴與未來價格污染。CLI RUN與READ逐位元一致，見cli-verification.json。Chrome151.0.7922.34新36檢查PASS：4組日期方向、截止／事後、6行表、9行敏感度、390／1400無頁面溢出、放大在圖內捲動、真JSON與SVG精確下載、0JS錯誤／外部請求。不是Android實機。

首次資料驗證發現兩筆無報價，改為保留null並拒絕受影響窗；首次圖面有圖例壓K線與末日期重疊，已移圖例、疏日期並重建後重跑瀏覽器。10,000股早期工程試算發現25%不整張，最終改20,000股並重跑研究與真實資料驗證，不沿用9939或32作最終數目。原引擎／舊驗收不重跑。

圖面實看最終8月事後與1月截止K／量、兩個正向資金曲線（初輪後只有本金設定更新）、手機頂部與K量截圖；其餘圖由相同固定producer產生，非宣稱逐張Android驗收。標準Python核心無新增第三方依賴；繪圖需matplotlib及明選CJK字型ROTATION_CJK_FONT，瀏覽器需Playwright與ROTATION_BROWSER。

重現：
```bash
python3 -m unittest rotation_research.test_core -v
python3 -m rotation_research.study
python3 -m rotation_research.verify_study
ROTATION_CJK_FONT=/path/to/CJK-font.otf python3 -m rotation_research.build_report
ROTATION_BROWSER=/path/to/chromium node rotation_research/verify_browser.cjs
```

報告金融資格：CONDITIONAL_PRICE_ONLY_NOT_TOTAL_RETURN，classification NOT_VALIDATED、rotation_policy NOT_APPROVED。分項完成不等於正式股利帳／資產管理／投資驗證完成。
