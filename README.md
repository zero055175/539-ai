# 539 AI V28.0 雲端研究版
1. 解壓縮，將本資料夾的內容（包括隱藏的 `.github`）放入新的 GitHub 儲存庫根目錄，使用預設分支。
2. Settings → Pages → Build and deployment → Source 選 GitHub Actions。確認 Actions 已啟用且允許工作流程寫入儲存庫；分支保護不可阻止機器人提交資料。
3. Actions → Sync historical data and deploy Pages → Run workflow。首次資料同步採分批補抓，可能需多次手動執行或等待排程。查看日誌與網頁未完成月份。不要把缺月為零當作完整性證明：目前只檢查月份有資料，未逐期核對。
4. 部署成功後使用 Pages 顯示的網址。每日 13:30 UTC（台灣 21:30）排程；GitHub 可能延遲或停用不活躍儲存庫排程。
5. 雲端網頁載入 docs/data/history.json，不需 Python 或 API Key。GitHub Actions 使用 Python 標準函式庫。公開儲存庫/Pages 資料可能公開，勿上傳私人資料或金鑰。
6. 靜態網站不提供 SQLite 寫入、Python 背景回測、即時觸發伺服器更新等功能；保留原瀏覽器研究模組。若要本機功能，另附未修改的 V27 ZIP。
7. 上游資料介面可能失效或限流；第二來源僅近期核對。快照初始為空，未提供預載真實資料。人工模擬與實際資料不得混用。歷史研究不代表預測能力。

## V29.0 報告管理
完成全部整合研究後自動保存至本機 localStorage，最多100筆且受瀏覽器容量限制；失敗會提示。亦可手動保存部分研究。JSON 備份可跨裝置還原。公開雲端索引位於 docs/data/reports/index.json，需維護者自行更新；不會自動上傳私人研究報告。HTTPS 或 localhost 才能建立資料指紋。

## V30.0 自動雲端研究
同步成功後，Actions 執行 research_cloud.py。至少300期才研究，六種模型採固定100期窗口、80/20時序切分，輸出命中分布、信賴區間及校正 p 值。相同資料指紋跳過重算。研究失敗記錄狀態；同步失敗則工作流程停止並保留既有網站。歷史資料可能缺漏，報告非獨立前瞻證據。雲端只自動執行六模型回測，其餘既有進階模組仍需瀏覽器操作。公開報告不包含私人本機紀錄。尚未實際部署或驗證官方連線。

## V31.0 每日研究樣本
每日台灣時間12:00（週一至週六）及21:30同步。20:00後不建立當日樣本；資料不足、前一期缺漏或同步錯誤時跳過。固定100期頻率模型僅作盲測，無可靠預測優勢。每日樣本在JSON中保留，事後核對命中數；Git紀錄不是可信第三方時間戳。部署既有倉庫時只更新 docs/index.html、daily31.py、.github/workflows/sync-pages.yml，不覆蓋既有 history.json 或報告。daily31.json 首次執行自動建立。排程可能延遲，特殊開獎日期尚未串接官方日曆。

## V32.0
新增 research32.py 與 docs/data/benchmark32.json。升級時只替換 docs/index.html、.github/workflows/sync-pages.yml，並新增 research32.py 與初始 benchmark32.json（若已有則保留）。原歷史及每日紀錄不可覆蓋。需先完成 V31.0；Actions 執行後讀取九模型統一回測。

## V33.0
新增固定歷史保留集封存。更新 research33.py、docs/index.html、.github/workflows/sync-pages.yml；保留原有資料與 validation33_lock.json。首次資料完整性檢查通過才封存。歷史資料不保證未被先前模型看過；真正前瞻測試尚未實施。

## V34.0
新增 research34.py，七模型前瞻性研究。預設19:00前封存，300期固定檢定；不代表可預測公平開獎。增量套件不覆蓋歷史資料。保留 prospective34.json。Git 時間非第三方證明。

## V35.0
新增 research35.py，固定首300期，Holm校正、Wilson個別區間、保守Bonferroni檢定力情境。未滿300期不公布檢定p值。增量更新保留全部既有JSON；GitHub封存非第三方時間證明。

## V36.0
新增 research36.py、stability36.json（自動生成），30/90/180/365個已核對期數、Wilson區間、非重疊30期波動、滾動範圍。資料不足不補值；沿用V35封存核對，僅描述統計，不作模型推薦或重複顯著性檢定。增量更新保留所有JSON。

## V37.0 封存稽核
新增 research37.py，保留舊協議及資料。預設僅比對 SHA-256。選用 RFC3161：在 GitHub repository variables 設定 TSA_URL（可信 HTTPS TSA 端點）及 TSA_CA_FILE（儲存庫內經獨立確認的可信 CA PEM 路徑）；未配置不會聲稱有第三方時間證明。時間戳以封存 SHA-256 的 ASCII 字串為資料，透過 OpenSSL 驗證簽章、憑證及資料指紋，保存 DER 回應於 docs/data/timestamp37。晚於研究截止的時間戳不可作為開獎前證明。保留所有既有 JSON。尚未連線測試真實 TSA。


## V38.0
新增 research38.py：歷史相鄰開獎重疊診斷、80/20 時序切分、非重疊30期區塊、100次公平模擬、前綴一致性測試。只輸出總體統計，不代表預測模型驗證。保留歷史資料，不覆蓋既有 JSON。

## V39.0 研究品質監測
執行 python research39.py，產生 docs/data/monitor39.json。新增報告讀取、同步品質、封存異常與描述性波動警示。5百分點為人工警示門檻，不是正式檢定。保留原資料；不自動選擇模型。

## V40.0 整合研究中心
- 保留 V39 完整原始模組，新增 research40.py 統一執行 V30–39，記錄個別退出狀態及報告 SHA-256。雜湊不是第三方證明。
- GitHub Actions 每日沿用原排程；研究子程序錯誤仍發布整合異常報告（同步本身失敗則不部署）。
- V39 升級僅覆蓋增量套件四個檔案。從 V30 升級則補齊完整套件所有 Python 程式、首頁及 workflow；保留遠端 docs/data 中既有資料，缺少的初始檔案才新增。
- 完整套件含空白初始資料，切勿覆蓋已累積資料。GitHub Pages Source 選 GitHub Actions，手動 Run workflow。
- 本版未驗證官方資料來源、特殊開獎日、TSA 或正式雲端部署；無預測優勢證據。
