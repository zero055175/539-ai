539 統計研究王 V41.0 Lite — 增量安裝

現有 539-ai 儲存庫不需刪除。先備份，僅更新下列三個檔案：
1. lite41.py → 根目錄
2. docs/index.html → docs/index.html
3. .github/workflows/sync-pages.yml → .github/workflows/sync-pages.yml
不要覆蓋或刪除 docs/data/history.json、daily31.json 或其他既有研究報告。
README_V41.txt、test_lite41.py 是說明及本機測試，不必上傳。
更新後確認 Settings > Pages > Source = GitHub Actions，前往 Actions 手動 Run workflow。
新工作流程只執行 lite41.py，舊研究模組不再執行，但原檔仍保留。
每日台灣時間約 12:00（週一至六）及 21:30（每日）觸發，排程可能延遲。
報告自動寫入 docs/data/lite41.json；原始 history.json 保留有效資料並合併新資料。
單一月份 API 沿用 V40.1；每次優先最近5個月，再補4個歷史月份；無需第二來源或年度ZIP。
來源失敗時保留舊資料，顯示錯誤。有效筆數不足仍可查看頻率，不虛構資料。
樣本採最近最多100筆有效歷史紀錄的固定頻率（同次數按號碼排序），至少10筆，且前一預設開獎日及近14日預設開獎日資料齊全；19:00後不建立當日樣本。週一至六為預設日曆，未核對特殊開獎日。舊樣本不覆寫；本版另存樣本，不混用舊模型紀錄。
僅供統計研究，無已證實預測優勢。雜湊並非第三方時間證明。
本機測試：python -m unittest -v test_lite41（6項人工資料測試）。實際 API、GitHub 部署及瀏覽器完整測試未完成。
