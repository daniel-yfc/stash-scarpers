# Live Walkthrough QA 報告 — 2026-10-08

7 站 browser walkthrough（匿名＋登入），每站 3–5 個商品頁，
驗證 scraper selector 對 live DOM 的符合度。

- 執行方式：browser task，唯讀（未購買／下載／註冊；登入僅用 Vault 既存憑證）
- 對應 commit：`dd393c2`（修正）、`99c49a1`（修正前）

---

## 一、搜尋關鍵字

| 站 | 種付け | 学生 | 中出 | 備註 |
|---|---|---|---|---|
| ACCEED | 45 件 | — | 93 件 | 匿名可搜尋；詳情頁需登入 |
| KO Video | 有結果 | 135 件 | 有結果 | — |
| KO Shop | 169 件 | 374 件 | 266 件 | — |
| KO Tube | 545 件 | 1412 件 | 739 件 | — |
| CK Download | 719 件 | — | — | 未另試其他關鍵字 |
| Men's Rush TV | 968 件 | — | — | 未另試其他關鍵字 |
| Hunk's Channel | 752 件 | 2902 件 | — | — |

---

## 二、商品連結

### ACCEED（登入後驗證）

- https://acceed.jp/detail.ACST425.html（串流，IKUZE）
- https://acceed.jp/detail.ACSM357.html（DVD，IKUZE21）
- https://acceed.jp/detail.ACST391.html（串流，BLACK HOLE）

### KO Video

- https://ko-video.com/products/detail.php?product_code=KG518_DVD
- https://ko-video.com/products/detail.php?product_code=KKE0304_DVD
- https://ko-video.com/products/detail.php?product_code=KEA039_DVD

### KO Shop

- https://www.ko-shop.com/products/detail.php?product_id=42791
- https://www.ko-shop.com/products/detail.php?product_id=42792
- https://www.ko-shop.com/products/detail.php?product_id=42784

### KO Tube（4 單品＋1 套裝）

- https://www.ko-tube.com/product/index/95991
- https://www.ko-tube.com/product/index/82590
- https://www.ko-tube.com/package/index/26987
- https://www.ko-tube.com/product/index/89554
- https://www.ko-tube.com/product/index/81619

### CK Download（登入後驗證）

- https://www.ck-download.com/product/detail/34416
- https://www.ck-download.com/product/detail/21628
- https://www.ck-download.com/product/detail/19363

### Men's Rush TV

- https://www.mensrush.tv/single.php?id=HAR-184_DL
- https://www.mensrush.tv/single.php?id=ARGA-134_DL
- https://www.mensrush.tv/single.php?id=FANS-1638_DL
- https://www.mensrush.tv/single.php?id=JSDV-103_DL

### Hunk's Channel

- https://www.hunk-ch.com/movie_detail.php?code=ACD-180&search_flag=all
- https://www.hunk-ch.com/movie_detail.php?code=JTS-JT014S5B&search_flag=all
- https://www.hunk-ch.com/movie_detail.php?code=IDS-115031&search_flag=all

---

## 三、問題清單與修正方式

### ACCEED（`scrapers/ACCEED.yml`）

| # | 問題 | 修正 |
|---|---|---|
| 1 | Date 只匹配 `DVD発売`；串流商品標籤為 `配信開始`，日期永遠抓不到 | selector 放寬為 `contains(.,'発売') or contains(.,'配信')` |
| — | 匿名詳情頁一律導向 login.php（比選擇器失效更嚴重） | 文件註記：需登入態＋斷言 `div#content4`，避免靜默寫入髒資料 |

### KO Video（`scrapers/KOVideo.yml`）

| # | 問題 | 修正 |
|---|---|---|
| 1 | bxSlider 複製 `li.bx-clone` 節點，第一個 `a.fancybox` 可能指向 `/gallery/` 圖片 | Image 排除 `li[not(contains(@class,'bx-clone'))]`（原已有 `/gallery/` 排除） |
| 2 | Performers 區塊有兩種格式（`男子学園モデル` h3＋外部連結／`出演モデル`＋`model_detail.php`），部分頁無 | `$performers` 改三式 union，欄位維持可選 |
| — | 詳情頁實際用 `?product_code=`（`?product_id=` 會進錯誤頁） | 確認：scraper 跟隨站內連結、不拼裝 URL，無需改 |

### KO Shop（`scrapers/KOShop.yml`）

| # | 問題 | 修正 |
|---|---|---|
| 1 | Details 太寬，會混入サンプル画像、アイコン説明、関連商品 | 縮窄到 `div.ma_b30` 內 `商品説明` h2 之後的 div |
| — | 全站無出演者欄位（名僅在説明自由文字） | 維持 CAST 文字解析備援（缺值即空，不報錯） |
| — | `dd` 值前置 ` : `（`&nbsp;`） | 確認：Code／Date 後處理已 strip，無需改 |

### KO Tube（`scrapers/KOTube.yml`）

| # | 問題 | 修正 |
|---|---|---|
| 1 | 套裝頁 `_3.jpg` 替代式誤抓 `#include_title` 內收錄作品縮圖 | 排除 `ancestor::*[@id='include_title']` |
| — | `btn_dvd` 僅存少數外部連結；多數改 `btn_to_pack`（站內套裝頁） | 記錄，未改（Code 語意不變） |
| — | 套裝頁無作品番号／プレイ／モデル欄 | 記錄，未改（容錯已存在） |

### CK Download（`scrapers/CK-Download.yml`）

| # | 問題 | 修正 |
|---|---|---|
| 1 | Title：th 實際為 `DVDタイトル`（無空格）；`//h1` 抓到網站標語 | th 比對去空格；`//h1` 改 `//div[@id='Contents']/h3`；td 為空時 fallback h3 |
| 2 | Image：`img[pred][1]` 的 `[1]` 是每父元素第一個（回傳集合）；文件順序首圖在 `li.clone` 內 | 改 `(…/li[not(contains(@class,'clone'))]//img…)[1]/@src`；src 為 protocol-relative，後處理已補 `https:` |

### Men's Rush TV（`scrapers/MensRushTV.yml`）

| # | 問題 | 修正 |
|---|---|---|
| 1 | Studio 取 `[1]`，ARGA-134_DL 一頁有兩家廠商 | 收集全部 `maid` 連結 |
| 2 | Details 只取 `p[1]`；ARGA-134_DL 為短摘要＋全文雙段落 | 改取 `h3[1]` 後全部 `p` |
| — | Date／Performers 選擇器失效（頁面無此欄位） | 維持可選（缺值即空），未改 |
| — | `//video[1]/@poster` 永遠取不到（播放器為 `img.no-save`） | 現行 union 已含 img 備援，未改 |

### Hunk's Channel（`scrapers/HunkCh.yml`）

| # | 問題 | 修正 |
|---|---|---|
| 1 | FlexSlider 在 live DOM 注入 `li.clone`，首圖變成複製品（先前誤抓 `_big20.jpg` 類圖片的根因） | Image／FrontImage 排除 `li[not(contains(@class,'clone'))]` |
| 2 | Duration 空白：`$data` 含換行，正則 `^.*?$` 無 `(?s)` 跨不了行（根因） | 加 `(?s)` |
| 3 | Code 僅靠 canonical／og:url | 加 `input[name='code']` 備援，並 strip `_STINF` 後綴 |

---

## 四、共通模式

FlexSlider／bxSlider 的 `li.clone` 輪播複製品在 4 站造成圖片選擇器誤判
（HunkCh、CK-Download、KOVideo、KOTube）。修正一律為排除 clone 節點；
server-side 抓取（無 JS）理論上無 clone，但 live DOM 驗證仍應排除。

---

## 五、驗證

- `node validator/index.mjs -a --ci`：通過
- `bash tools/validate-all.sh`：16/16 通過
- `python3 tools/check_scraper_semantics.py`：通過
- `python3 -m pytest tools/tests/ -q`：30/30 通過
