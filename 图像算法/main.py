from __future__ import annotations

import argparse
import sys

from src.config import ConfigError, load_config
from src.detector import DetectorError, ensure_model
from src.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smart Campus image algorithm runner")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--image", default=None, help="Run one image instead of scanning images/")
    parser.add_argument("--dry-run", action="store_true", help="Do not write Redis/MySQL, only generate local outputs")
    parser.add_argument("--skip-mysql", action="store_true", help="Skip MySQL read/write and use fallback seats")
    parser.add_argument("--skip-redis", action="store_true", help="Skip Redis read/write")
    parser.add_argument("--download-model-only", action="store_true", help="Download model and exit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        if args.download_model_only:
            ensure_model(config["paths"]["model"], auto_download=True)
            print(f"Model ready: {config['paths']['model']}")
            return 0

        results = run_pipeline(
            config=config,
            dry_run=args.dry_run,
            skip_mysql=args.skip_mysql,
            skip_redis=args.skip_redis,
            single_image=args.image,
        )
        print(f"Finished. Generated {len(results)} seat result rows.")
        return 0 if results else 2
    except (ConfigError, DetectorError) as exc:
        print(f"[ERROR] {exc}")
        return 1
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())

