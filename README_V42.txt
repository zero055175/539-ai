539 統計研究王 V42.0 Lite — 可信度強化版

V41 已安裝者：只上傳 lite42.py 到根目錄、docs/index.html 到 docs、.github/workflows/sync-pages.yml 到 .github/workflows。保留既有 lite41.py（V42 依賴它）、docs/data/history.json、docs/data/lite41.json 及所有其他歷史資料。若不確定 lite41.py 是否正確，本套件附原始 V41 檔案。README 及 test 檔案不必上傳。先備份再更新。
設定 Pages Source = GitHub Actions；手動 Run workflow。新版執行 lite42.py，沿用 V41 單來源同步及封存規則，另寫 docs/data/lite42.json。網址不變。
固定每日樣本規則不變，至少10筆有效資料、前一預設開獎日與近期14日預設開獎日齊全，且未到19:00。早期缺漏不阻擋。舊樣本仍保留，不因本版更新而重新生成。首頁只顯示台灣當日樣本，過往樣本在下方。每次同步失敗保留舊資料。
新增：固定規則逐期歷史回測、固定種子隨機對照、2/3/4/5支以上理論與觀察統計、前瞻個別Wilson 95%區間、兩號及三號共現摘要、貝氏邊際平滑估計（20期等效先驗）、199次全域頻率蒙地卡羅檢定、資料品質報告及資料指紋快取。新增統計不參與每日樣本選取；不以歷史最佳模型作預測。歷史回測不是真正獨立前瞻驗證，缺期可能影響結果；單一頻率檢定不能證明獨立性或預測優勢。無外部付費服務。週一至六預設日曆未核對特殊開獎日。
本機驗證：python -m unittest -v test_lite41 test_lite42（14項人工資料測試）；python -m py_compile lite41.py lite42.py test_lite42.py；新增網頁 JS 語法檢查。實際 API、GitHub部署與完整瀏覽器操作未驗證。
