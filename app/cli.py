import argparse, asyncio, json
from pathlib import Path
from .models import CandidateProfile
from .pipeline import scrape_and_store, get_ranked, export_to_csv
from .email_harvester import build_email_list

def _load_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def cmd_scrape(args):
    cfg = _load_json(args.config)
    stats = asyncio.run(scrape_and_store(cfg))
    print(f"Inserted {stats['inserted']} new opportunities (fetched {stats['fetched']}).")

def cmd_rank(args):
    prof = _load_json(args.profile)
    profile = CandidateProfile(**prof)
    triples = get_ranked(profile, limit=args.limit)
    for i,(o,s,_) in enumerate(triples[:args.top],1):
        print(f"{i:>2}. [{s:.2f}] {o.company} — {o.title} ({o.location or 'N/A'})")
        print(f"    {o.apply_url}")
    if args.export:
        export_to_csv(triples, Path(args.export), top_k=args.top)
        print(f"Exported top {args.top} to {args.export}")

def cmd_emails(args):
    prof = _load_json(args.profile)
    profile = CandidateProfile(**prof)
    out = Path(args.out)
    info = build_email_list(profile, limit=args.limit, csv_path=out)
    print(f"Harvested {info['count']} rows. CSV: {info['path']}")

def main():
    parser = argparse.ArgumentParser(prog="easyintern")
    sub = parser.add_subparsers()

    p1 = sub.add_parser("scrape", help="Scrape sources and store to DB")
    p1.add_argument("--config", required=True)
    p1.set_defaults(func=cmd_scrape)

    p2 = sub.add_parser("rank", help="Rank stored opportunities")
    p2.add_argument("--profile", required=True)
    p2.add_argument("--limit", type=int, default=200)
    p2.add_argument("--top", type=int, default=50)
    p2.add_argument("--export", type=str, default="")
    p2.set_defaults(func=cmd_rank)

    p3 = sub.add_parser("emails", help="Harvest emails for top-ranked opportunities")
    p3.add_argument("--profile", required=True)
    p3.add_argument("--limit", type=int, default=50)
    p3.add_argument("--out", type=str, default="exports/emails.csv")
    p3.set_defaults(func=cmd_emails)

    args = parser.parse_args()
    if hasattr(args, "func"): args.func(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()
