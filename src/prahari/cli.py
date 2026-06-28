"""Prahari command-line interface.

Subcommands::

    build-data      Phase 1  unify Kaggle corpora -> data/processed/dataset.csv
    augment         Phase 3  add synthetic digital-arrest examples to the dataset
    train           Phase 4  train the detector -> models/prahari_model.joblib
    evaluate        Phase 4  evaluate on the held-out split, write reports/
    predict         Phase 4  score a single message from the command line
    serve           Phase 5  launch the FastAPI server
    gen-fixtures    Phase 6  write synthetic labelled test fixtures

Typical first run (no Kaggle data needed for a demo)::

    prahari augment        # builds a dataset (synthetic if data/raw is empty)
    prahari train
    prahari evaluate
    prahari predict "You are under digital arrest, share the OTP now"
    prahari serve
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from prahari import config


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


# --------------------------------------------------------------------------- #
# Command handlers
# --------------------------------------------------------------------------- #
def _cmd_build_data(args) -> int:
    from prahari.data.load import build_dataset

    config.ensure_dirs()
    config.set_global_seed()
    raw_dir = args.raw_dir or config.RAW_DIR
    _df, summary = build_dataset(raw_dir=raw_dir, out_path=args.out)
    return 0 if summary["rows"] > 0 else 1


def _cmd_augment(args) -> int:
    from prahari.data.load import build_dataset
    from prahari.generator import generate

    config.ensure_dirs()
    config.set_global_seed()
    extra = generate(n_scam=args.n_scam, n_legit=args.n_legit, seed=config.RANDOM_SEED)
    print(f"Generated {len(extra)} synthetic examples "
          f"({args.n_scam} scam / {args.n_legit} legit target).")
    _df, summary = build_dataset(raw_dir=args.raw_dir, out_path=args.out, extra=extra)
    return 0 if summary["rows"] > 0 else 1


def _cmd_train(args) -> int:
    from prahari.models.train import train

    train(out_path=args.out, test_size=args.test_size, seed=args.seed)
    return 0


def _cmd_evaluate(args) -> int:
    from prahari.models.evaluate import evaluate

    evaluate(model_path=str(args.model) if args.model else None)
    return 0


def _cmd_predict(args) -> int:
    from prahari.models.predict import format_report, predict

    text = args.text or (sys.stdin.read() if not sys.stdin.isatty() else "")
    if not text.strip():
        print("Provide a message: prahari predict \"<text>\"  (or pipe via stdin).")
        return 2
    try:
        result = predict(text, model_path=str(args.model) if args.model else None)
    except FileNotFoundError as exc:
        print(exc)
        return 1
    if args.json:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_report(result))
    return 0


def _cmd_serve(args) -> int:
    import uvicorn

    print(f"Starting Prahari on http://{args.host}:{args.port}  "
          f"(web UI at /app, docs at /docs)")
    uvicorn.run("prahari.api.server:app", host=args.host, port=args.port,
                reload=args.reload)
    return 0


def _cmd_gen_fixtures(args) -> int:
    from prahari.generator import generate

    config.ensure_dirs()
    # A dedicated seed keeps fixtures disjoint from training augmentation.
    df = generate(n_scam=args.n_scam, n_legit=args.n_legit, seed=config.RANDOM_SEED + 1)
    out = args.out or (config.FIXTURES_DIR / "fixtures.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} fixtures -> {out}")
    return 0


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prahari", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    bd = sub.add_parser("build-data", help="Unify Kaggle corpora into one dataset.")
    bd.add_argument("--raw-dir", type=_path, default=None,
                    help="Directory holding the raw Kaggle CSVs (default: data/raw).")
    bd.add_argument("--out", type=_path, default=None,
                    help="Output CSV path (default: data/processed/dataset.csv).")
    bd.set_defaults(func=_cmd_build_data)

    ag = sub.add_parser("augment", help="Add synthetic digital-arrest examples.")
    ag.add_argument("--raw-dir", type=_path, default=None)
    ag.add_argument("--out", type=_path, default=None)
    ag.add_argument("--n-scam", type=int, default=600)
    ag.add_argument("--n-legit", type=int, default=600)
    ag.set_defaults(func=_cmd_augment)

    tr = sub.add_parser("train", help="Train the detector.")
    tr.add_argument("--out", type=_path, default=None,
                    help="Model artifact path (default: models/prahari_model.joblib).")
    tr.add_argument("--test-size", type=float, default=0.2)
    tr.add_argument("--seed", type=int, default=config.RANDOM_SEED)
    tr.set_defaults(func=_cmd_train)

    ev = sub.add_parser("evaluate", help="Evaluate the model, write reports/.")
    ev.add_argument("--model", type=_path, default=None)
    ev.set_defaults(func=_cmd_evaluate)

    pr = sub.add_parser("predict", help="Score a single message.")
    pr.add_argument("text", nargs="?", default="", help="Message text to score.")
    pr.add_argument("--model", type=_path, default=None)
    pr.add_argument("--json", action="store_true", help="Emit JSON instead of a report.")
    pr.set_defaults(func=_cmd_predict)

    sv = sub.add_parser("serve", help="Launch the FastAPI server.")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8000)
    sv.add_argument("--reload", action="store_true")
    sv.set_defaults(func=_cmd_serve)

    gf = sub.add_parser("gen-fixtures", help="Write synthetic test fixtures.")
    gf.add_argument("--out", type=_path, default=None)
    gf.add_argument("--n-scam", type=int, default=60)
    gf.add_argument("--n-legit", type=int, default=60)
    gf.set_defaults(func=_cmd_gen_fixtures)

    return p


def _force_utf8_stdout() -> None:
    """Make stdout/stderr UTF-8 so reports with ₹, •, ⚠ don't crash on a
    Windows cp1252 console. Best-effort; ignored where streams can't reconfigure.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover - non-reconfigurable stream
            pass


def main(argv=None) -> int:
    _force_utf8_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
