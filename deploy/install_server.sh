#!/usr/bin/env bash
# 在服务器上以 root 执行: bash deploy/install_server.sh
# 需先把仓库放到 /opt/relay-probe（或改下面的 APP_ROOT）

set -euo pipefail
APP_ROOT="${APP_ROOT:-/opt/relay-probe}"
cd "$APP_ROOT"

if [[ ! -f "requirements.txt" ]]; then
  echo "在 $APP_ROOT 未找到 requirements.txt，请先把仓库 clone 到此处。"
  exit 1
fi

apt-get update -y
apt-get install -y python3 python3-venv python3-pip

python3 -m venv .venv
# shellcheck source=/dev/null
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [[ -f "deploy/relay-probe.service" ]]; then
  install -m 0644 deploy/relay-probe.service /etc/systemd/system/relay-probe.service
  systemctl daemon-reload
  systemctl enable relay-probe.service
  systemctl restart relay-probe.service
  systemctl --no-pager -l status relay-probe.service || true
fi

echo "若尚未配置 /opt/relay-probe/.env，请从 .env.example 复制后填写，再执行: systemctl restart relay-probe"
