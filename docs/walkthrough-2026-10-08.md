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

---

## 六、第二輪驗證（2026-10-08）

新關鍵字：童顏／生徒／発展。每站 ≥3 件**與第一輪不同**的商品，
驗證修正後（`dd393c2`）的 selector。

### KO Tube

關鍵字筆數：童顏 514 件、生徒 306 件、発展 640 件。

| 頁面 | URL | Image（修正版） | 其他 |
|---|---|---|---|
| A（套裝） | https://www.ko-tube.com/package/index/28498 | MATCH（`_C.jpg`，經 pack_photo 分支） | Code/Tags NO MATCH（套裝頁固無此欄） |
| B（單品） | https://www.ko-tube.com/product/index/95764 | MATCH（`_3.jpg`，分支二） | 全 MATCH |
| C（套裝） | https://www.ko-tube.com/package/index/28207 | MATCH（`_C.jpg`；`#include_title` 縮圖已被排除） | Code/Tags NO MATCH（套裝頁固有） |

裁定：**fix confirmed**。套裝頁 pack_photo 在文件順序上先於 `#include_title`，
union 首命中必為 `_C.jpg` 封面。Code／Tags 在套裝頁的 NO MATCH 屬頁面結構
差異（套裝頁無作品番号／プレイ列），非 selector 失效。

次要發現：單品頁 bxSlider 首個 li 為 bx-clone，union 首命中可能為 `-20_3.jpg`
而非 `-01_3.jpg`（仍為該作品主圖，資料正確）。

### KO Video

關鍵字筆數：童顏 73 件、生徒 87 件、発展 144 件。

| 頁面 | URL | Image（修正版） | Performers（修正版） |
|---|---|---|---|
| 1 | …/detail.php?product_code=KKE0318_DVD | MATCH（排除 bx-clone，取到封面 jpg） | 三分支皆 NO MATCH（本頁無演員連結） |
| 2 | …/detail.php?product_code=KERO250_DVD | MATCH | 分支 1 MATCH（5 名） |
| 3 | …/detail.php?product_code=KLIN034_DVD | MATCH | 分支 1 MATCH（2 名） |

裁定：**Image fix confirmed**（3 頁皆正確取到封面）。Performers 分支 1 確認；
新發現：實際演員連結為 `/products/model.php?model_id=`，`model_detail.php`
分支疑似 dead branch —— 已追加 `model.php?model_id=` 分支（commit 待）。
Title／Date／Studio／Tags／Details 抽查 3 頁全 MATCH。

### CK Download（登入後驗證）

關鍵字筆數：童顏 483 件、生徒 175 件、発展 471 件。

| 頁面 | URL | Image（修正版） | Title（修正版） |
|---|---|---|---|
| 1 | /product/detail/34285 | MATCH（`_1.jpg`，排除 clone） | MATCH（td 空 → h3 退回） |
| 2 | /product/detail/33993 | MATCH（`_1.jpg`） | MATCH（td 空 → h3 退回） |
| 3 | /product/detail/27171 | MATCH（`_1.jpg`） | MATCH（th 主分支命中） |

裁定：**兩項 fix 皆 confirmed**。Image 排除 `li.clone` 後 3 頁皆回傳單一
真實封面 `_1.jpg`；Title 的 `DVDタイトル`（無空格）比對正確，td 為空時退回
h3（兩頁驗證），td 非空時命中主分支（一頁驗證）。編號／日期／工作室／
タグ／簡介抽查 3 頁全 MATCH。

### KO Shop

關鍵字筆數：童顏 126 件、生徒 122 件、発展 189 件。

| 頁面 | URL | Details（修正版 v1） |
|---|---|---|
| P1 | …/detail.php?product_id=40722 | v1 NO MATCH（見下） |
| P2 | …/detail.php?product_id=42509 | v1 NO MATCH（見下） |
| P3 | …/detail.php?product_id=41012 | v1 NO MATCH（見下） |

**v1 修正仍壞掉**，兩個原因：(a) class 比對字串 `' under_col '`／`' ma_b30 '`
含前後空白，但 `contains(@class,…)` 未包 `concat(' ',normalize-space(@class),' ')`，
實際 class 恰為 `under_col`／`ma_b30` 時永不成立；(b) 即使修掉空白，
`h2/following-sibling::div[1]` 仍無結果 —— 說明文字是 `div.ma_b30` 的直接
文字節點（＋`<br>`），h2 後並無 div 兄弟節點。

**v2 修正**：`//div[contains(concat(' ',normalize-space(@class),' '),' under_col ')]/div[contains(concat(' ',normalize-space(@class),' '),' ma_b30 ')][h2[contains(.,'商品説明')]]/text()[normalize-space()]`
—— 取 `div.ma_b30` 的直接文字節點，可排除內層宣傳連結／樣本圖／相關商品文字。
Title／Code／Date／Image／Studio／Tags 抽查 3 頁全 MATCH。

### Men's Rush TV

關鍵字筆數：童顏 851 件、生徒 109 件、発展 273 件。

| 頁面 | URL | Studio（修正版） | Details（修正版） |
|---|---|---|---|
| 1 | single.php?id=ACD-163_DL | MATCH（1 家全取） | MATCH（長描述＋宣傳段） |
| 2 | single.php?id=STR-451_DL | MATCH（1 家全取） | MATCH（短摘要＋全文雙段落——最具證明力） |
| 3 | single.php?id=DIG-104_DL | MATCH（1 家全取） | MATCH（LINEUP＋宣傳段） |
| 4 | single.php?id=CAPY-1083_DL | MATCH（1 家全取） | MATCH（長描述＋宣傳段） |

裁定：**Details fix confirmed**（STR-451_DL 證明雙段落皆取到，舊版只取第一段）。
**Studio fix 結構上確認**（移除 `[1]` 後按文件順序回傳全部 `maid` 連結）；
雙廠商同列情境本輪未再遇到（第一輪 ARGA-134_DL 為證），留待端到端確認。
Title／Code／Tags／Image 抽查 4 頁全 MATCH，無迴歸。

### ACCEED（登入後驗證）

關鍵字筆數：童顏 35 件、生徒 14 件、発展 31 件。
安全：描述含「10代」「幼さ残る」等結果一律跳過未開。

| 頁面 | URL | 關鍵結果 |
|---|---|---|
| 1（DVD） | detail.ACSM114.html | 8 選擇器全 MATCH；日期標籤 `DVD発売(配信開始)` |
| 2（DVD） | detail.ACSM186.html | 8 選擇器全 MATCH |
| 3（串流） | detail.ACST384.html | Date MATCH（`配信開始`）；Details NO MATCH；Studio 無此欄 |
| 4（串流） | detail.ACST319.html | Date MATCH（`配信開始`）；Details NO MATCH；Studio 無此欄 |

裁定：**Date fix confirmed**（串流 `配信開始` 與 DVD 合併標籤皆命中）。
**Details 在串流模板仍漏抓**：簡介改包在 `div.chitiet > p` 而非裸文字節點
—— 已追加 `//div[contains(@class,'chitiet')]//text()[normalize-space()]` 聯集（v2）。
Studio 在串流頁根本無 `シリーズ` 欄（欄位不存在，非 selector 問題）。
Title／Code／Image／Tags／Performers 4 頁全 MATCH。

### Hunk's Channel

關鍵字筆數：童顏 463 件、生徒 114 件、発展 243 件。

| 頁面 | URL | Image（修正版 v1） | Duration（修正版） | Code（修正版） |
|---|---|---|---|---|
| 1 | …/movie_detail.php?code=SB-N0533 | NO MATCH（見下） | MATCH（23 分） | MATCH |
| 2 | …/movie_detail.php?code=IDS-105274 | NO MATCH（見下） | MATCH（26 分） | MATCH |
| 3 | …/movie_detail.php?code=KO-BEAST184 | NO MATCH（見下） | MATCH（128 分） | MATCH |
| 4 | …/movie_detail.php?code=ACD-171 | NO MATCH（見下） | MATCH（23 分） | MATCH |

**Image v1 仍壞掉**：`"… | //meta[@property='og:image']/@content"` 開頭括號 `(` 未閉合，
XPath 語法無效（schema validator 不檢查 XPath 語法，故 CI 未攔截）。
clone 排除邏輯本身驗證正確（`li[not(contains(@class,'clone'))][1]` 正確跳過首個 clone li）；
`contains(concat(' ',normalize-space(@class),' '),' flexslider ')` 的 token 比對亦正確。
**v2 修正**：補上結尾 `)`。Title（h2）4 頁全 MATCH。
備註：src 為相對路徑（`./video/img/…`），Stash 會以頁面 URL absolutize；
`og:url` 分支 4 頁皆不存在，保留作無害備援。

## 第二輪最終裁定

7 站 × 3 新關鍵字（童顏／生徒／発展）× 3–4 新商品頁，共 23 頁，全部驗證完畢。

| 站 | 第一輪修正 | 第二輪結果 | V2 |
|---|---|---|---|
| KO Tube | Image 排除 `#include_title` 縮圖 | confirmed（3 頁） | — |
| KO Video | Image 排除 bx-clone；Performers 多版型 | Image confirmed；Performers 追加 `model.php?model_id=` 分支 | ✅ |
| CK Download | Title `DVDタイトル`＋h3；Image 排除 clone | 兩項皆 confirmed（3 頁，主／退回分支全觸發） | — |
| KO Shop | Details 限「商品説明」後 div | v1 仍壞（class 空白＋無 div 兄弟）；v2 改取 `div.ma_b30` 直接文字節點 | ✅ |
| Men's Rush TV | Studio 全取；Details 全段落 | 兩項皆 confirmed（4 頁） | — |
| ACCEED | Date 兼顧発売／配信 | Date confirmed；Details 串流模板追加 `div.chitiet` 備援 | ✅ |
| Hunk's Channel | Image 排除 clone；Duration `(?s)`；Code hidden input | Duration／Code confirmed；Image v1 括號未閉合 → v2 補 `)` | ✅ |

教訓：schema validator 不檢查 XPath 語法；`contains(@class,' padded ')` 類字串
必須搭配 `concat(' ',normalize-space(@class),' ')`，否則單一 token 的 class
屬性永不命中。兩處皆為同類錯誤，v2 已修。
