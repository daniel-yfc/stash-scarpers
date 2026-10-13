# Tailscale Egress — 怎麼連到 Stash

Task 腳本（`tasks/` 下五支）都經 `tasks/stash_client.py` 連 Stash。
本文件說明連線鏈路與 proxy 規則；程式碼以本文件為準。

## 鏈路

Stash 在私人 LAN 內，不直接對外。腳本經以下鏈路連它：

```
task 腳本 → curl → egress proxy（同主機的 Tailscale egress port）→ Tailscale → Stash
```

- Stash 位址只由 `STASH_URL` 環境變數給，預設為 localhost placeholder。
  真實位址只在執行時由環境提供，**絕不寫進 repo**。
- 一般 egress proxy（`HTTPS_PROXY` 環境變數）指向通用出口，port `3128`。
  通用出口到不了私人 LAN；Stash 流量必須走**同一 proxy 主機的 port `3130`**
 （Tailscale egress port）。

## `stash_client.py` 的 proxy 規則

優先順序：

1. `STASH_PROXY` 若有設定，原封不動傳給 `curl --proxy`（不改寫）。
   用它可跳過下面的 port 改寫。
2. 否則用 `HTTPS_PROXY`，**只把 port 換成 `3130`**，
   scheme、auth、host 全部保留（以 `urlparse` 解析後重組，非字串切掉重接）。
3. 兩者皆未設定時，不傳 `--proxy`（空 `--proxy` 會失敗，
   且失敗常以 JSON parse error 的樣子冒出來，難以追查）。

> 為什麼不直接原封不動傳 `HTTPS_PROXY`？
> 原封不動會把 Stash 請求送到 `:3128`（通用出口），到不了私人 LAN，
> 連線就會失敗。`:3130` 改寫是鏈路需求，不是裝飾。

## 錯誤處理

- `curl` 非零 exit，或回應不是 JSON，丟 `StashConnectionError`
  （不再是看不懂的 `JSONDecodeError`）。
- `STASH_URL`、`STASH_PROXY`、`HTTPS_PROXY` 皆在每次呼叫時才從環境變數讀取，
  不快取（環境的 proxy 認證可能輪換）。

## 執行方式

```sh
export STASH_URL=http://<stash-host>:9999/graphql
# 選用：跳過 port 改寫，直接指定完整 proxy URL
# export STASH_PROXY=http://<proxy-host>:3130
python3 tasks/doctor.py
```

真實位址與 token 只放環境變數，不要寫進 repo、不要貼到 issue／PR。
