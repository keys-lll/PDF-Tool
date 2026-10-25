# PDF 併頁器 v1.1.0

這個版本新增 Windows 10／11 x64 可攜版，並讓縮圖在沒有 poppler 的系統上
也能運作。Linux、Windows 與 git 版本歷史都包含在這次發佈中。

## 下載

- `PDF-Page-Merger-1.1.0-windows-x64.zip` — Windows 免安裝可攜版
- `pdf-page-merger_1.1.0-1_all.deb` — Debian／Ubuntu 安裝套件
- `SHA256SUMS` — 下載檔完整性校驗

## Windows 使用方式

1. 下載並解壓縮 `PDF-Page-Merger-1.1.0-windows-x64.zip`。
2. 執行 `PDF-Page-Merger` 資料夾內的 `PDF-Page-Merger.exe`。
3. 保留 `_internal` 資料夾，不要只複製 exe。

不需要安裝 Python 或 poppler。這是未簽章執行檔，SmartScreen 可能顯示警告；
確認下載來源後可選擇「更多資訊」→「仍要執行」。

## Linux 安裝或升級

```bash
sudo apt install ./pdf-page-merger_1.1.0-1_all.deb
```

## 本版變更

- 新增 Windows 可攜版與 GitHub Actions 建置流程。
- 新增內建 PDFium 縮圖後端，Windows 縮圖不再依賴外部 poppler。
- 依平台選擇中文介面字型（Windows 使用 Microsoft JhengHei UI）。
- 新增凍結應用程式的建置後 smoke test。
- 將所有 PDFium 呼叫序列化，避免 Windows 多執行緒縮圖時發生原生當機。
- 合併與密碼流程沿用 1.0.1 的進度對話框競態修正。
- 測試總數為 24 項，涵蓋 PDFium 縮圖、跨執行緒序列化、取消、拖曳、解鎖與合併。

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
