"""Download Inside Airbnb data for the active city defined in config/cities.yml.

Design notes
------------
* Config-driven: switch `active_city` in the YAML (or pass --city) to fetch a
  different city later with zero code changes.
* Safe to re-run: files that already exist are skipped.
* Atomic writes: data is streamed to a ``.part`` file and renamed only on
  success, so an interrupted download never leaves a half-written CSV behind.

Usage
-----
    python src/download_data.py            # uses active_city from the config
    python src/download_data.py --city barcelona
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "cities.yml"
CHUNK = 1 << 20  # 1 MiB per streamed chunk


def load_config(city: str | None):
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    city = city or cfg["active_city"]
    if city not in cfg["cities"]:
        sys.exit(f"City '{city}' not in {CONFIG_PATH}. Available: {list(cfg['cities'])}")
    return city, cfg["cities"][city]


def build_targets(c: dict) -> list[tuple[str, str]]:
    """Return (url, filename) pairs for every file we need."""
    base = c["base_url"].rstrip("/")
    root = f"{base}/{c['country']}/{c['region']}/{c['city_slug']}/{c['snapshot_date']}"
    targets = []
    for fname in c["files"]["detailed"]:
        targets.append((f"{root}/data/{fname}", fname))
    for fname in c["files"]["visualisations"]:
        targets.append((f"{root}/visualisations/{fname}", fname))
    return targets


def download(url: str, dest: Path) -> bool:
    if dest.exists():
        print(f"  = {dest.name} already present ({dest.stat().st_size/1e6:.1f} MB) - skipping")
        return True
    try:
        with requests.get(url, stream=True, timeout=60,
                          headers={"User-Agent": "airbnb-assignment/1.0"}) as r:
            if r.status_code == 404:
                print(f"  x {dest.name}: 404 Not Found")
                print(f"      tried: {url}")
                print("      -> snapshot date/path may have moved. Open the Get-the-Data page,")
                print("         right-click this file, 'Copy link', and update config/cities.yml.")
                return False
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            tmp = dest.with_suffix(dest.suffix + ".part")
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(CHUNK):
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        print(f"\r  v {dest.name}: {done/1e6:6.1f}/{total/1e6:.1f} MB "
                              f"({done/total*100:5.1f}%)", end="")
                    else:
                        print(f"\r  v {dest.name}: {done/1e6:6.1f} MB", end="")
            tmp.rename(dest)
            print(f"\r  v {dest.name}: {done/1e6:.1f} MB                              ")
            return True
    except requests.RequestException as e:
        print(f"  x {dest.name}: {e}")
        return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Download Inside Airbnb data.")
    ap.add_argument("--city", help="Override active_city from the config.")
    args = ap.parse_args()

    city, c = load_config(args.city)
    out_dir = PROJECT_ROOT / "data" / "raw" / city
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {c['name']} - snapshot {c['snapshot_date']}")
    print(f"Destination: {out_dir}\n")

    results = [download(url, out_dir / name) for url, name in build_targets(c)]
    ok = sum(results)
    print(f"\nDone: {ok}/{len(results)} files downloaded into {out_dir}")
    if ok < len(results):
        print("Some files failed - resolve the messages above before continuing.")
        sys.exit(1)


if __name__ == "__main__":
    main()
