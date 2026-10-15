"""
DESNIVEL — Batch Sonic Visualization
=====================================
Genera i plot sonori per TUTTE le 12 tappe.

Uso:
    .venv/bin/python visualize_all_sonic.py
    .venv/bin/python visualize_all_sonic.py --dpi 100  # più veloce, per preview
"""

import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
VIZ_DIR = PROJECT_DIR / "output" / "viz"


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=12)
    args = parser.parse_args()

    VIZ_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generando plot sonori per tappe {args.start}–{args.end}...")
    print(f"Output: {VIZ_DIR}/\n")

    failed = []
    for tappa_num in range(args.start, args.end + 1):
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "src/visualize_sonic.py",
                    str(tappa_num),
                    "--dpi", str(args.dpi),
                ],
                cwd=str(PROJECT_DIR),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                # Estrai il messaggio di salvataggio
                lines = result.stdout.strip().split("\n")
                print(f"  tappa {tappa_num:>2d} ✓")
            else:
                print(f"  tappa {tappa_num:>2d} ✗ {result.stderr[:50]}")
                failed.append(tappa_num)
        except subprocess.TimeoutExpired:
            print(f"  tappa {tappa_num:>2d} ✗ timeout")
            failed.append(tappa_num)
        except Exception as e:
            print(f"  tappa {tappa_num:>2d} ✗ {str(e)[:50]}")
            failed.append(tappa_num)

    print()
    if failed:
        print(f"⚠ {len(failed)} tappa(e) fallita(e): {failed}")
        return 1
    else:
        # Count files
        pngs = list(VIZ_DIR.glob("tappa_*_sonic.png"))
        total_size = sum(p.stat().st_size for p in pngs) / 1024 / 1024
        print(f"✓ Tutte {len(pngs)} tappe visualizzate ({total_size:.1f} MB)")
        print(f"  Apri: {VIZ_DIR}/")
        return 0


if __name__ == "__main__":
    sys.exit(main())
