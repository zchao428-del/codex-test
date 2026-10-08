import argparse
import json
from pathlib import Path
from .pipeline import run

def main():
    parser = argparse.ArgumentParser(description="360-point radial compensation prototype")
    parser.add_argument("input", type=Path)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        report = run(args.input, json.loads(args.config.read_text(encoding="utf-8")), args.output)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
