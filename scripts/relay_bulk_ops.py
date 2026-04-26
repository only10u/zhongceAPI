"""运维：批量设定掺水展示文案、清空站点登记价格（日榜「1人民币=…」列）。

在项目根目录执行::

    python scripts/relay_bulk_ops.py --dilution-almost-none --clear-site-price
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from relay_probe.database import SessionLocal  # noqa: E402
from relay_probe.models import Relay  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Relay 表批量维护")
    ap.add_argument(
        "--dilution-almost-none",
        action="store_true",
        help="将所有站点掺水展示设为「几乎没有掺水」，并清空 dilution_override",
    )
    ap.add_argument(
        "--clear-site-price",
        action="store_true",
        help="清空所有站点 site_price（排行「1人民币=x Token」登记）",
    )
    args = ap.parse_args()
    if not args.dilution_almost_none and not args.clear_site_price:
        ap.print_help()
        sys.exit(1)

    db = SessionLocal()
    touched = 0
    try:
        for r in db.query(Relay).order_by(Relay.id).all():
            dirty = False
            if args.dilution_almost_none:
                if r.dilution_label != "几乎没有掺水" or r.dilution_override is not None:
                    r.dilution_label = "几乎没有掺水"
                    r.dilution_override = None
                    dirty = True
            if args.clear_site_price and r.site_price:
                r.site_price = None
                dirty = True
            if dirty:
                touched += 1
        db.commit()
        print(f"已提交：共更新 {touched} 条 relay 记录。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
