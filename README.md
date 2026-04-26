# API 中转站探测服务（海外检测站）

对 **OpenAI 兼容** 网关发起轻量 `GET`（默认 `/v1/models`），记录延迟、HTTP 状态，可选定时后台探测。

## 本机开发

```bash
python3 -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env
python -m uvicorn relay_probe.main:app --host 0.0.0.0 --port 8765
```

- 健康检查: `GET http://127.0.0.1:8765/health`
- 上次结果: `GET http://127.0.0.1:8765/api/last`
- 立即探测: `POST http://127.0.0.1:8765/api/check`

## 推送到你的 Git 仓库

在**本机**项目目录中（将 `你的仓库地址` 换成实际 URL）:

```bash
cd "项目路径"
git init
git add .
git commit -m "chore: initial relay probe"
git branch -M main
git remote add origin <你的仓库地址>
git push -u origin main
```

若远程已有仓库，使用平台提供的 `git clone` 地址即可。

## 部署到海外服务器（DMIT LAX 等）

1. SSH 登录: `ssh root@154.17.25.199`（示例 IP，以你面板为准）
2. 安装 git（若未装）: `apt-get update && apt-get install -y git`
3. 克隆**私有库**时需在服务器配置 SSH key 或 HTTPS token，见 GitHub/GitLab 文档
4. 建议路径:

```bash
git clone <你的仓库地址> /opt/relay-probe
cd /opt/relay-probe
cp .env.example .env
nano .env   # 填写 RELAY_BASE_URL、RELAY_API_KEY 等
```

5. 安装为 systemd 服务（脚本会建 venv 并装依赖）:

```bash
bash deploy/install_server.sh
```

6. 更新代码后:

```bash
cd /opt/relay-probe
git pull
./.venv/bin/pip install -r requirements.txt
systemctl restart relay-probe
```

**注意:** 你截图里该实例 CPU/内存已较高，探测服务本身很轻，但若与其它重负载同机，请留意；防火墙安全组中按需开放 `8765` 或前面加 Nginx 只暴露 443。

## 环境变量

见 `.env.example`。

- `CHECK_INTERVAL_SEC=0`：不自动轮询，仅 `POST /api/check` 或外部 cron 调用
- `CHECK_INTERVAL_SEC=60`：每 60 秒后台探测一次

## 安全

- 勿将 `.env` 提交到 Git
- 探测用 Key 与主业务 Key 分离
