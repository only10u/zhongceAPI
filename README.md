# 多中转站 API 探测与排名（zhongceAPI）

在海外节点对 **多个** OpenAI 兼容网关做 `GET` 探测（默认 `/v1/models`），样本写入 **SQLite**，按统计窗口计算 **成功率 / 平均延迟** 并给出 **排名**。提供简单 **Web 看板** 与 JSON API。

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

- **看板**: 浏览器打开 `http://127.0.0.1:8765/`
- **排名 JSON**: `GET /api/ranking?window_hours=24`
- **API 文档**: `http://127.0.0.1:8765/docs`

### 环境变量（`.env`）——「第五步」怎么填

全局**不**再配置单一路径 `RELAY_BASE_URL`；多中转在 **API / 数据库** 里维护。在服务器上 `nano /opt/relay-probe/.env` 时重点看这些：

| 变量 | 怎么填 |
|------|--------|
| **`RANKING_WINDOW_HOURS`** | 用 **几小时** 内的探测样本来算「窗口成功率、平均延迟」。例如填 **`24`** 表示统计**最近 24 小时**；看短期波动可改小。 |
| **`ADMIN_TOKEN`** | 自己生成一段**长随机**口令（可 `openssl rand -hex 32`），填在等号后。**增删改中转**的接口要带头 `X-Admin-Token: 这段口令`。不填则**任何人**都能改你中转列表，仅适合本机/内网。 |
| **`RANKING_PIN_FIRST_BASES`** | 逗号分隔的 **`https://` 根地址**（可不要尾 `/`），这些站点在**排名排序时始终排在最前**；展示的成功率、延迟**仍是真实探测数据**，不伪造。示例：`RANKING_PIN_FIRST_BASES=https://dapicloud.com` |
| `DATA_DIR` | 数据目录，默认 `data`，库在 `data/app.db` |
| `HTTP_TIMEOUT_SEC` | 单次 `GET` 超时秒数 |
| `CHECK_INTERVAL_SEC` | `0` 不自动轮询；`>0` 为每轮全量探测后休眠秒数 |
| `SAMPLE_RETENTION_DAYS` | 更早的样本会删，控库体积 |
| `HOST` / `PORT` | 监听地址与端口（与 systemd 里要一致） |

在数据库里，单条中转还可设可选字段 **`rank_boost`**（越大越靠前，API 的 `POST/PATCH` 可带），与 `RANKING_PIN_FIRST_BASES` 可叠加；仍**不会**把成功率改为假的 100%。

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

## 推送到 GitHub 与服务器

```bash
git remote add origin git@github.com:only10u/zhongceAPI.git   # 若未添加
git add -A && git commit -m "..." && git push origin main
```

服务器上 `git pull` 后安装依赖并重启服务（见 `deploy/install_server.sh`）。**务必备份** `data/app.db` 再覆盖代码，避免误删数据目录。

## 安全

- 勿将 `.env` 与 `data/` 提交到 Git
- 生产环境务必设置强 `ADMIN_TOKEN`，并限制管理接口仅内网或反代 + 鉴权
