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

### 环境变量（`.env`）

全局**不再**配置「单一」`RELAY_BASE_URL`；中转列表通过 **API 写入数据库**（见下）。

| 变量 | 含义 |
|------|------|
| `DATA_DIR` | SQLite 与数据目录，默认 `data`（库文件 `data/app.db`） |
| `HTTP_TIMEOUT_SEC` | 单次 GET 超时 |
| `CHECK_INTERVAL_SEC` | `0` 不后台轮询；`>0` 为每轮「所有已启用中转」探完后的休眠秒数 |
| `RANKING_WINDOW_HOURS` | 默认统计窗口（小时），`GET /api/ranking` 可用参数覆盖 |
| `SAMPLE_RETENTION_DAYS` | 删除超过该天数的探测样本 |
| `HOST` / `PORT` | 服务监听 |
| `ADMIN_TOKEN` | 若设置，则增删改中转需请求头 `X-Admin-Token`；不设置则写接口对任意客户端开放（仅建议内网/测试） |

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
