# 版本歷程

本專案遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/)，格式參考
[Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)。

## [Unreleased]

## [1.1.1] - 2026-10-27

### Fixed

- 修正長檔名加密 PDF 在開啟密碼對話框時，因 `ElidedLabel` 版面重入造成的閃退。

### Tests

- 新增長檔名加密 PDF 的密碼對話框回歸測試，總數 25 項。

## [1.1.0] - 2026-10-26

### Added

- 新增 Windows 10／11 x64 可攜版，使用 PyInstaller 打包為免安裝 zip。
- 新增 PDFium（pypdfium2）縮圖後端；Windows 不需要安裝 poppler。
- 依平台選擇中文字型（Windows 使用 Microsoft JhengHei UI）。
- 新增 packaged application 的 `--smoke-test` 自我檢查。
- 新增 Windows GitHub Actions 建置與測試流程。

### Fixed

- 將所有 PDFium 呼叫序列化，避免 Windows 背景縮圖執行緒同時存取時發生原生當機。

### Changed

- Python 執行期需求加入 pypdfium2 與 Pillow；Linux 套件仍優先使用 poppler。
- 測試總數增加至 24 項，包含 PDFium 跨執行緒序列化測試。

## [1.0.1] - 2026-10-25

### Fixed

- 修正合併完成或取消時，進度對話框已關閉仍更新標籤所造成的 `AttributeError`。

### Tests

- 新增進度對話框重入情境的回歸測試，總計 21 項。

## [1.0.0] - 2026-10-25

### Added

- 支援一次加入多份 PDF，或以拖放方式加入檔案。
- 以縮圖畫廊呈現所有來源頁面，可直接拖曳即時換位，靠近上下邊緣會自動捲動。
- 提供「上移」「下移」按鈕、多選頁面刪除與鍵盤快速鍵。
- 加密 PDF 逐檔詢問密碼；支援錯誤重試、取消後保留來源，以及稍後再解鎖。
- 使用 poppler 在背景產生縮圖，不阻塞主介面；可取消並自動清理。
- 依目前頁序合併 PDF，寫入暫存檔後原子替換，避免產生半成品。
- 合併前提醒尚未解鎖的 PDF，並可選擇繼續或取消。
- 提供 Debian／Ubuntu `.deb`，包含桌面選單、SVG／PNG icon、man page 與文件。
- 加入 20 項自動化測試，涵蓋加密、縮圖、拖曳排序、錯誤處理與合併輸出。

### Security

- PDF 密碼只保留在記憶體中，不寫入專案、設定檔或日誌。
- 解密後的工作副本放在權限 `0700` 的 `/tmp/pdf-page-merger-*`，正常結束時刪除。
- 來源 PDF 不會被修改；合併輸出為新的未加密 PDF。

### Known limitations

- 合併結果不保證保留書籤、表單欄位、附件或數位簽章。
- `.deb` 依賴 Ubuntu 26.04／Debian 的 PySide6、pypdf 與 poppler 套件名稱。
- 未提供 Windows 或 macOS 安裝檔。
