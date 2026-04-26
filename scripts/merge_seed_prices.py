"""把 _prices_export.json 的 site_price 按 base_url 合并进 seed_sites.json"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed_sites.json"
PRICES = ROOT / "data" / "_prices_export.json"


def norm_url(u: str) -> str:
    return (u or "").strip().rstrip("/").lower()


def main() -> None:
    seeds = json.loads(SEED.read_text(encoding="utf-8"))
    px = json.loads(PRICES.read_text(encoding="utf-8"))["sites"]
    by_url = {norm_url(p["base_url"] or ""): p.get("site_price") or "" for p in px if p.get("base_url")}

    for item in seeds:
        bu = norm_url(item.get("base_url", ""))
        sp = by_url.get(bu, "")
        item["price"] = sp if sp else "—"

    out = json.dumps(seeds, ensure_ascii=False, indent=2)
    out_path = ROOT / "data" / "seed_sites.merged.json"
    out_path.write_text(out + "\n", encoding="utf-8")
    print(out_path.as_posix())


if __name__ == "__main__":
    main()
