#!/usr/bin/env python
"""Interactive Enterprise MLOps Demo.

This script walks through the complete model lifecycle demonstrating:
- Clean developer experience (local iteration)
- CI/CD staging training (simulated PR workflow)
- Champion/Challenger validation
- Model promotion with governance
- Cross-workspace production deployment
- Production batch inference

New demo flow (mirrors GitHub Actions):

  enterprise-dev-staging workspace                    enterprise-production workspace
  ┌─────────────────────────────────────────┐        ┌─────────────────────────────┐
  │ Ch1: Train locally (dev-stack)          │        │                             │
  │ Ch2: Simulate PR → staging training     │        │                             │
  │ Ch3: Champion/Challenger comparison     │        │                             │
  │ Ch4: Promote to staging + explore MCP   │        │                             │
  │ Ch5: Export model ─────────────────────────────▶ │ Ch5: Import model           │
  │                                         │        │      (set to production)    │
  │                                         │        │ Ch6: Batch inference        │
  └─────────────────────────────────────────┘        └─────────────────────────────┘

Run the full demo:
    python demo/run_demo.py

Run specific chapter:
    python demo/run_demo.py --chapter 2

List chapters:
    python demo/run_demo.py --list

Single-workspace fallback:
    python demo/run_demo.py --workspace-mode single-workspace
"""

import sys
from pathlib import Path

import click

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env if available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from demo.workspace_utils import (
    DEV_STAGING,
    PRODUCTION,
    is_two_workspace_mode,
    switch_workspace,
    verify_workspace_credentials,
)


CHAPTERS = {
    1: ("Train Locally", "chapter_1_training"),
    2: ("Simulate PR → Staging Training", "chapter_2_staging_training"),
    3: ("Champion vs Challenger", "chapter_3_champion_challenger"),
    4: ("Promote to Staging", "chapter_4_promote_staging"),
    5: ("Promote to Production", "chapter_5_promote_production"),
    6: ("Run Batch Inference", "chapter_6_batch_inference"),
}

# Chapters 1-5 run in dev-staging, chapter 6 runs in production
PRODUCTION_CHAPTERS = {6}


def print_banner():
    """Print demo banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              🏥  ENTERPRISE MLOps DEMO  🏥                                ║
║                                                                           ║
║          Binary Classification Risk Prediction                            ║
║          Complete Model Lifecycle & Promotion Flow                        ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_chapter_header(num: int, title: str):
    """Print chapter header."""
    print(f"\n{'=' * 75}")
    print(f"  CHAPTER {num}: {title.upper()}")
    print(f"{'=' * 75}\n")


def wait_for_continue():
    """Wait for user to press Enter."""
    input("\n⏎  Press Enter to continue...")


def print_workspace_flow():
    """Print the 2-workspace demo flow diagram."""
    print(
        """
  This demo mirrors the GitHub Actions CI/CD flow:

  enterprise-dev-staging                    enterprise-production
  ┌───────────────────────────────┐        ┌─────────────────────────────┐
  │ Ch1: Train locally (dev)      │        │                             │
  │ Ch2: Simulate PR → staging    │        │                             │
  │ Ch3: Champion vs Challenger   │        │                             │
  │ Ch4: Promote to staging       │        │                             │
  │ Ch5: Export model ────────────────────▶│ Ch5: Import model           │
  │                               │        │      (set to production)    │
  │                               │        │ Ch6: Batch inference        │
  └───────────────────────────────┘        └─────────────────────────────┘

  GitHub Actions alignment:
    Ch1-2  →  train-staging.yml (PR triggers staging training)
    Ch3    →  test-batch-inference.yml (validates model)
    Ch4    →  Merge PR (promotes to staging)
    Ch5    →  promote-to-production.yml (GitHub Release)
    Ch6    →  batch-inference.yml (daily cron)
"""
    )


def setup_workspace_for_chapter(chapter_num: int, two_workspace: bool) -> bool:
    """Switch to the correct workspace for the given chapter."""
    if not two_workspace:
        return True

    target = PRODUCTION if chapter_num in PRODUCTION_CHAPTERS else DEV_STAGING
    if switch_workspace(target):
        return True
    return False


def run_chapter(num: int, two_workspace: bool):
    """Run a specific chapter with workspace context."""
    if num == 1:
        from demo.chapters.chapter_1_training import run
    elif num == 2:
        from demo.chapters.chapter_2_staging_training import run
    elif num == 3:
        from demo.chapters.chapter_3_champion_challenger import run
    elif num == 4:
        from demo.chapters.chapter_4_promote_staging import run
    elif num == 5:
        from demo.chapters.chapter_5_promote_production import run
    elif num == 6:
        from demo.chapters.chapter_6_batch_inference import run
    else:
        print(f"Unknown chapter: {num}")
        return

    # Pass workspace mode to chapters that need it
    if num in (5, 6):
        run(two_workspace=two_workspace)
    else:
        run()


@click.command()
@click.option(
    "--chapter",
    "-c",
    type=int,
    default=None,
    help="Run specific chapter (1-6)",
)
@click.option(
    "--list",
    "-l",
    "list_chapters",
    is_flag=True,
    help="List all chapters",
)
@click.option(
    "--auto",
    "-a",
    is_flag=True,
    help="Auto-advance without prompts",
)
@click.option(
    "--workspace-mode",
    "-w",
    type=click.Choice(["two-workspace", "single-workspace"]),
    default=None,
    help="Workspace mode (auto-detected if not set)",
)
def main(chapter: int, list_chapters: bool, auto: bool, workspace_mode: str):
    """Run the Enterprise MLOps demo."""
    if list_chapters:
        print("\n📚 Demo Chapters:\n")
        for num, (title, _) in CHAPTERS.items():
            print(f"   {num}. {title}")
        print("\nRun with: python demo/run_demo.py --chapter <num>\n")
        return

    # Determine workspace mode
    if workspace_mode == "two-workspace":
        two_workspace = True
    elif workspace_mode == "single-workspace":
        two_workspace = False
    else:
        two_workspace = is_two_workspace_mode()

    print_banner()

    # Print workspace mode info
    if two_workspace:
        print("  Mode: 2-Workspace (enterprise-dev-staging + enterprise-production)")
        print_workspace_flow()
    else:
        print("  Mode: Single-Workspace (all chapters in current workspace)")
        creds = verify_workspace_credentials()
        missing = [name for name, ok in creds.items() if not ok]
        if missing:
            print(f"  (Missing credentials for: {', '.join(missing)})")
            print("  Set ZENML_DEV_STAGING_URL/API_KEY and ZENML_PRODUCTION_URL/API_KEY")
            print("  in .env to enable 2-workspace mode.\n")
        print()

    if chapter:
        if chapter not in CHAPTERS:
            print(f"Invalid chapter: {chapter}. Choose 1-{len(CHAPTERS)}")
            return
        title, _ = CHAPTERS[chapter]
        print_chapter_header(chapter, title)
        if not setup_workspace_for_chapter(chapter, two_workspace):
            return
        run_chapter(chapter, two_workspace)
    else:
        print("This demo walks through the complete model lifecycle.\n")
        print("📚 Chapters:")
        for num, (title, _) in CHAPTERS.items():
            ws = "production" if num in PRODUCTION_CHAPTERS else "dev-staging"
            marker = f" [{ws}]" if two_workspace else ""
            print(f"   {num}. {title}{marker}")

        if not auto:
            wait_for_continue()

        for num in sorted(CHAPTERS.keys()):
            title, _ = CHAPTERS[num]
            print_chapter_header(num, title)
            if not setup_workspace_for_chapter(num, two_workspace):
                print("  Skipping chapter due to workspace setup failure.")
                continue
            run_chapter(num, two_workspace)

            if not auto and num < len(CHAPTERS):
                wait_for_continue()

    print("\n" + "=" * 75)
    print("  DEMO COMPLETE")
    print("=" * 75)
    print("\nNext steps:")
    print("   - View dashboard: zenml login")
    print("   - See docs: docs/ARCHITECTURE.md")
    print()


if __name__ == "__main__":
    main()
