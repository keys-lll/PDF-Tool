# PDF 併頁器 v1.1.1

修正 Windows 與 Linux 版在開啟「長檔名加密 PDF」時，密碼對話框造成程式閃退的問題。
這是 v1.1.0 的修正版，建議所有使用者升級。

## 下載

- `PDF-Page-Merger-1.1.1-windows-x64.zip` — Windows 免安裝可攜版
- `pdf-page-merger_1.1.1-1_all.deb` — Debian／Ubuntu 安裝套件
- `SHA256SUMS` — 下載檔完整性校驗

## Windows 使用方式

1. 解壓縮 `PDF-Page-Merger-1.1.1-windows-x64.zip`。
2. 執行 `PDF-Page-Merger` 資料夾內的 `PDF-Page-Merger.exe`。
3. 保留 `_internal` 資料夾，不要只複製 exe。

不需要安裝 Python 或 poppler。這是未簽章執行檔，SmartScreen 可能顯示警告；
確認下載來源後可選擇「更多資訊」→「仍要執行」。

## Linux 安裝或升級

```bash
sudo apt install ./pdf-page-merger_1.1.1-1_all.deb
```

## 修正內容

- 長檔名會讓來源列的 `ElidedLabel` 在 `resizeEvent` 內更新文字，並再次觸發布面
  配置；開啟密碼對話框時可能遞迴到 `RecursionError` 或原生 segfault。
- 現在加入重入保護，並避免標籤文字影響水平版面配置。
- 新增長檔名加密 PDF 的回歸測試；Linux 與 Windows 各 25 項測試通過。
- Windows 版持續包含 PDFium 縮圖引擎與 PDFium 跨執行緒序列化修正。

## 系統需求

- Windows：Windows 10／11 x64；免安裝，無需管理員權限。
- Linux：Python 3.10 以上；`python3-pyside6.qtwidgets`、`python3-pypdf`、
  `python3-cryptography`、`poppler-utils`。
- 建議 Linux 安裝 `fonts-noto-cjk` 與 `xdg-utils`。

## 驗證下載

```bash
sha256sum -c SHA256SUMS
```

## 已知限制

- 合併結果不保證保留書籤、表單欄位、附件或數位簽章。
- 輸出 PDF 不會重新加密。
- Windows 版本沒有數位簽章，可能觸發 SmartScreen 或防毒軟體警告。
- 尚未提供 macOS 版本或 Windows 安裝程式。

完整變更請見倉庫根目錄的 `CHANGELOG.md`。
