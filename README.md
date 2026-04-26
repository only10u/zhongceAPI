# 中测（zhongceAPI）— 中转站 API 检测平台

**中测**部署在**海外节点**（如你的 DMIT VPS），对 **多个** OpenAI 兼容网关做 `GET` 探测（默认 `/v1/models`），样本写入 **SQLite**，按统计窗口计算 **成功率 / 平均延迟** 并给出 **排名**。提供 **Web 看板** 与 JSON API。服务器主机名（如 `DAPI-new`）只是机器名，与产品名「中测」无关。

## 本机运行

```bash
python3 -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 按需编辑 .env（见下）
python -m uvicorn relay_probe.main:app --host 0.0.0.0 --port 8765
```

- **Web**: 首页 `/`，多模型排行 `/rank`（[禾维 Hvoy](https://hvoy.ai) / [TokensQC](https://tokensqc.com) 风格分栏，在线率/掺水/延迟/状态），受理收录 `/inclusion`（表单项参考 [Hvoy 联系页](https://hvoy.ai/contact) 习惯），`JWT_SECRET`+`INIT_ADMIN_*` 配置后使用 `/login` 与后台 `/admin`；静态资源在 `/static`。
- **JSON**: 总榜 `GET /api/ranking?window_hours=`（1–744 小时）；多模型分榜 `GET /api/dashboard?window_hours=`；排行页合并拉取 `GET /api/rank-bundles`（日 24h / 周 168h / 月 720h 三套）
- **OpenAPI**: `http://127.0.0.1:8765/docs`

**说明：** 「掺水率」在深度对话探针未接入前为 **—** 或库表字段 `dilution_override`；**在线率/延迟** 来自对 `GET /v1/models` 的响应中是否**子串匹配**各模型线号（见 `relay_probe/model_catalog.py`），与商业质检站全量能力可能不同。

**批量增加站点（含参考 [Hvoy](https://hvoy.ai) 首页表）：** 将 JSON 数组写入 `data/seed_sites.json`（格式见 `data/seed_sites.example.json`），重启后执行一次 `POST /api/admin/reseed` 并带 `X-Admin-Token`，或仅重启（若 `seed_sites.json` 非空，启动时会尝试导入未存在的 Base）。

### 环境变量（`.env`）——「第五步」怎么填

全局**不**再配置单一路径 `RELAY_BASE_URL`；多中转在 **API / 数据库** 里维护。在服务器上 `nano /opt/relay-probe/.env` 时重点看这些：

| 变量 | 怎么填 |
|------|--------|
| **`RANKING_WINDOW_HOURS`** | 用 **几小时** 内的探测样本来算「窗口成功率、平均延迟」**默认值**（首页/通用 API 未指定 `window_hours` 时）。可 **1–744** 小时。排行页本身固定为日 24h、周 168h、月 720h 三套。 |
| **`ADMIN_TOKEN`** | 自己生成一段**长随机**口令（可 `openssl rand -hex 32`），填在等号后。**增删改中转**的接口要带头 `X-Admin-Token: 这段口令`。不填则**任何人**都能改你中转列表，仅适合本机/内网。 |
| **`RANKING_PIN_FIRST_BASES`** | 逗号分隔的 **`https://` 根地址**（可不要尾 `/`），这些站点在**排名排序时始终排在最前**；展示的成功率、延迟**仍是真实探测数据**，不伪造。示例：`RANKING_PIN_FIRST_BASES=https://dapicloud.com` |
| `DATA_DIR` | 数据目录，默认 `data`，库在 `data/app.db` |
| `HTTP_TIMEOUT_SEC` | 单次 `GET` 超时秒数 |
| `CHECK_INTERVAL_SEC` | `0` 不自动轮询；`>0` 为每轮全量探测后休眠秒数 |
| `SAMPLE_RETENTION_DAYS` | 更早的样本会删，控库体积 |
| `HOST` / `PORT` | 监听地址与端口（与 systemd 里要一致） |
| **`PUBLIC_BASE_URL`** | 对外的站点根，无尾斜杠，如 `https://zhongapice.com`。填后：`/docs` 会显示该地址为 API 基址、页面会输出 `canonical`/`og:url`、且 **HTTPS 时**登录 Cookie 带 `Secure`。 |
| **`TRUSTED_HOSTS`** | 仅生产反代时建议设：允许访问的 `Host` 名，英文逗号分隔，如 `zhongapice.com,www.zhongapice.com`。不填不校验（适合本机）。 |
| `JWT_SECRET` | 必须设置，用于 Cookie 登录签名校验。 |
| `INIT_ADMIN_USERNAME` / `INIT_ADMIN_PASSWORD` | 仅当**尚无用户**时创建首个**管理员**账号（之后用 `/login` 进 `/admin`）。 |
| `ALLOW_REGISTER` | 默认 `true`：未登录用户可 `/login` 自助注册**普通**账号（`admin` 名保留给管理员注册拒绝）。 |

在数据库里，单条中转还可设可选字段 **`rank_boost` / `group_name` / `site_price` / `dilution_override`** 等，与 `RANKING_PIN_FIRST_BASES` 可组合使用。

### 管理中转（写操作）

```bash
# 新增（示例，需替换 base 与 token）
curl -sS -X POST "http://127.0.0.1:8765/api/relays" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: 你的ADMIN_TOKEN" \
  -d '{"name":"站点A","base_url":"https://gateway.example.com","api_key":"sk-xxx","check_path":"/v1/models","enabled":true}'
```

- `GET /api/relays`：列表（**不返回**具体 `api_key`，仅有 `has_api_key`）
- `PATCH /api/relays/{id}` / `DELETE /api/relays/{id}`：同样需 `X-Admin-Token`（若已配置）
- `POST /api/relays/{id}/check`：立即探测该条
- `POST /api/probe-all`：立即探测全部启用项

### 排名规则（简要）

在统计窗口内：对每条中转统计样本数、成功次数、成功率，以及**仅成功样本**的平均延迟；先按**成功率**降序，再按**平均延迟**升序；无样本的中转排在后面。

### 公网域名与 HTTPS（以 zhongapice.com 为例）

1. 在 DNS 为域名添加 **A/AAAA** 指向你的 VPS 公网 IP。  
2. 本机仍由 **Nginx、Caddy** 等反代到 `http://127.0.0.1:8765`（与 `PORT` 一致），反代上配置 **Let’s Encrypt** 等拿到证书，对外为 **443 HTTPS**。  
3. **把变量写进** 项目根目录的 **`.env` 文件**（不要只在终端里打 `KEY=value`，那不会持久、进程也读不到）：
   ```bash
   cd /opt/relay-probe
   nano .env   # 或 vim .env
   ```
   在文件中增加或修改（无尾斜杠）：
   ```env
   PUBLIC_BASE_URL=https://zhongapice.com
   TRUSTED_HOSTS=zhongapice.com,www.zhongapice.com
   ```
   保存后退出。若用 `www` 子域，DNS/证书中要与之一致或做 301 到主域。  
4. **重启** 跑中测的进程，环境变量才会重新加载。若使用仓库里的 systemd 单元，服务名一般是 **`relay-probe`**（见 `deploy/relay-probe.service`）：
   ```bash
   # 先确认实际单元名（你机器上可能不同）
   systemctl list-units --type=service --all | grep -iE 'relay|uvicorn|zhongce'

   sudo systemctl restart relay-probe
   sudo systemctl status relay-probe
   ```
   若未用 systemd、而是手动的 `uvicorn …`，需停掉原进程后**在 `/opt/relay-probe` 下**再执行：  
   `/opt/relay-probe/.venv/bin/uvicorn relay_probe.main:app --host 0.0.0.0 --port 8765`（或用你原来的启动方式）。  
5. 验证：浏览器打开 `https://zhongapice.com/docs`；页面「查看源」中应能见到指向 `https://zhongapice.com` 的 `canonical`（若已配置 `PUBLIC_BASE_URL`）。

## 推送到 GitHub 与服务器

```bash
git remote add origin git@github.com:only10u/zhongceAPI.git   # 若未添加
git add -A && git commit -m "..." && git push origin main
```

服务器上 `git pull` 后安装依赖并重启服务（见 `deploy/install_server.sh`）。**务必备份** `data/app.db` 再覆盖代码，避免误删数据目录。

## 安全

- 勿将 `.env` 与 `data/` 提交到 Git
- 生产环境务必设置强 `ADMIN_TOKEN`，并限制管理接口仅内网或反代 + 鉴权
