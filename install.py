#!/usr/bin/env python3
"""
install.py — Robust dependency installer for AI Interview Trainer
------------------------------------------------------------------
Handles large packages (sentence-transformers, chromadb) that often
time out when installed all at once.

Usage:
    python install.py            # full install
    python install.py --no-rag   # skip heavy RAG deps (chromadb + sentence-transformers)
"""

import subprocess
import sys
import argparse


# ── Package groups ────────────────────────────────────────────────────────────
CORE = [
    "flask==3.0.3",
    "python-dotenv==1.0.1",
    "werkzeug==3.0.3",
    "pdfplumber==0.11.4",
    "PyPDF2==3.0.1",
]

WATSONX = [
    "ibm-watsonx-ai==1.1.2",
]

RAG = [
    "numpy==1.26.4",
    "sentence-transformers==3.1.1",
    "chromadb==0.5.5",
]

PROD = [
    "gunicorn==22.0.0",
]


def pip_install(packages: list[str], label: str, retries: int = 3):
    """Install a list of packages one by one with timeout + retry."""
    print(f"\n{'='*60}")
    print(f"  Installing: {label}")
    print(f"{'='*60}")

    for pkg in packages:
        success = False
        for attempt in range(1, retries + 1):
            print(f"\n  [{attempt}/{retries}] {pkg} ...", end=" ", flush=True)
            result = subprocess.run(
                [
                    sys.executable, "-m", "pip", "install",
                    pkg,
                    "--timeout", "120",       # 120 s socket timeout per chunk
                    "--retries", "5",          # urllib3-level retries
                    "--progress-bar", "off",
                    "--quiet",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print("OK")
                success = True
                break
            else:
                print(f"FAILED (attempt {attempt})")
                if attempt < retries:
                    print(f"     Retrying...")
                else:
                    print(f"  ✗  Could not install {pkg}:")
                    print(result.stderr[-600:] if result.stderr else "(no output)")

        if not success:
            return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Install Interview Trainer dependencies")
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Skip heavy RAG packages (chromadb + sentence-transformers). "
             "The app will run without knowledge-base features.",
    )
    parser.add_argument(
        "--no-prod",
        action="store_true",
        help="Skip gunicorn (use Flask dev server only).",
    )
    args = parser.parse_args()

    # Upgrade pip first
    print("\nUpgrading pip...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
        check=False,
    )

    all_ok = True

    all_ok &= pip_install(CORE,    "Core Flask + PDF parsing")
    all_ok &= pip_install(WATSONX, "IBM watsonx.ai SDK")

    if not args.no_rag:
        all_ok &= pip_install(RAG, "RAG stack (numpy + sentence-transformers + chromadb)")
    else:
        print("\n  [--no-rag] Skipping RAG packages.")
        _patch_app_for_no_rag()

    if not args.no_prod:
        all_ok &= pip_install(PROD, "Production server (gunicorn)")

    print("\n")
    if all_ok:
        print("✅  All packages installed successfully!")
        print("    Run: python app.py")
    else:
        print("⚠️  Some packages failed. See errors above.")
        print("    Try running: python install.py  (again — pip will skip already-installed packages)")
        sys.exit(1)


def _patch_app_for_no_rag():
    """Print a reminder that RAG features will be disabled."""
    print("""
  NOTE: RAG packages were skipped.
  The app will start fine, but the Knowledge Base upload feature will
  show an error if used. All other features (resume parsing, question
  generation, prep tips) work without RAG.

  To add RAG later, run:
      pip install numpy==1.26.4 sentence-transformers==3.1.1 chromadb==0.5.5 \\
          --timeout 120 --retries 5
""")


if __name__ == "__main__":
    main()
