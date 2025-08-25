#!/usr/bin/env python3
import argparse
import os
import sys
import json
import time
from urllib.parse import urlparse

import requests


def detect_repo_type(repo_url: str) -> str:
    try:
        host = urlparse(repo_url).netloc.lower()
    except Exception:
        return "github"
    if "github" in host:
        return "github"
    if "gitlab" in host:
        return "gitlab"
    if "bitbucket" in host:
        return "bitbucket"
    if "codeberg" in host:
        return "codeberg"
    return "github"


def build_request_payload(args: argparse.Namespace) -> dict:
    messages = [{
        "role": "user",
        "content": args.prompt or "Create a concise overview of this repository and propose a wiki structure."
    }]
    payload = {
        "repo_url": args.url,
        "type": args.type or detect_repo_type(args.url),
        "messages": messages,
        "provider": args.provider,
        "model": args.model,
        "language": args.language,
    }
    if args.token:
        payload["token"] = args.token
    # Optional file filters
    if args.excluded_dirs:
        payload["excluded_dirs"] = args.excluded_dirs
    if args.excluded_files:
        payload["excluded_files"] = args.excluded_files
    if args.included_dirs:
        payload["included_dirs"] = args.included_dirs
    if args.included_files:
        payload["included_files"] = args.included_files
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Call DeepWiki backend chat stream to generate wiki content")
    parser.add_argument("--url", required=True, help="Repository URL (e.g., https://codeberg.org/owner/repo)")
    parser.add_argument("--provider", default=os.environ.get("DEEPWIKI_PROVIDER", "google"), help="Model provider")
    parser.add_argument("--model", default=os.environ.get("DEEPWIKI_MODEL", None), help="Model name (optional, uses default if omitted)")
    parser.add_argument("--language", default=os.environ.get("DEEPWIKI_LANG", "en"), help="Output language")
    parser.add_argument("--type", default=None, help="Repo type override: github|gitlab|bitbucket|codeberg")
    parser.add_argument("--token", default=os.environ.get("DEEPWIKI_TOKEN", ""), help="Access token if needed (optional)")
    parser.add_argument("--prompt", default=None, help="Override prompt content")
    parser.add_argument("--excluded-dirs", dest="excluded_dirs", default=None, help="Newline-separated excluded dirs")
    parser.add_argument("--excluded-files", dest="excluded_files", default=None, help="Newline-separated excluded files")
    parser.add_argument("--included-dirs", dest="included_dirs", default=None, help="Newline-separated included dirs")
    parser.add_argument("--included-files", dest="included_files", default=None, help="Newline-separated included files")
    parser.add_argument("--server", default=os.environ.get("SERVER_BASE_URL", "http://localhost:8001"), help="Backend server base URL")

    args = parser.parse_args()

    target = args.server.rstrip("/") + "/chat/completions/stream"
    payload = build_request_payload(args)

    print(f"POST {target}")
    print(f"Payload: {json.dumps({k: v for k, v in payload.items() if k != 'token'}, indent=2)}")

    with requests.post(target, json=payload, stream=True) as resp:
        if not resp.ok:
            print(f"Request failed: {resp.status_code} {resp.reason}", file=sys.stderr)
            try:
                print(resp.text, file=sys.stderr)
            except Exception:
                pass
            return 1

        try:
            for chunk in resp.iter_content(chunk_size=None):
                if not chunk:
                    continue
                sys.stdout.write(chunk.decode("utf-8", errors="ignore"))
                sys.stdout.flush()
        except KeyboardInterrupt:
            print("\nInterrupted.")
        except Exception as e:
            print(f"\nError reading stream: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


