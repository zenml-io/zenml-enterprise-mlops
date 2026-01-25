#!/usr/bin/env python
"""Interactive Enterprise MLOps Demo.

This script walks through the complete model lifecycle demonstrating:
- Clean developer experience
- Platform governance
- Model promotion flow (dev → staging → production)
- Champion/Challenger pattern
- Complete audit trails

Run the full demo:
    python demo/run_demo.py

Run specific chapter:
    python demo/run_demo.py --chapter 2

List chapters:
    python demo/run_demo.py --list
"""

import sys
from pathlib import Path

import click

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


CHAPTERS = {
    1: ("Train a Model", "chapter_1_training"),
    2: ("Explore Model Control Plane", "chapter_2_model_control_plane"),
    3: ("Promote to Staging", "chapter_3_promote_staging"),
    4: ("Champion vs Challenger", "chapter_4_champion_challenger"),
    5: ("Promote to Production", "chapter_5_promote_production"),
    6: ("Run Batch Inference", "chapter_6_batch_inference"),
}


def print_banner():
    """Print demo banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              🏥  ENTERPRISE MLOps DEMO  🏥                                ║
║                                                                           ║
║          Patient Readmission Risk Prediction                              ║
║          Model Lifecycle & Promotion Flow                                 ║
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


def run_chapter_1():
    """Chapter 1: Train a Model."""
    from demo.chapters.chapter_1_training import run

    run()


def run_chapter_2():
    """Chapter 2: Explore Model Control Plane."""
    from demo.chapters.chapter_2_model_control_plane import run

    run()


def run_chapter_3():
    """Chapter 3: Promote to Staging."""
    from demo.chapters.chapter_3_promote_staging import run

    run()


def run_chapter_4():
    """Chapter 4: Champion vs Challenger."""
    from demo.chapters.chapter_4_champion_challenger import run

    run()


def run_chapter_5():
    """Chapter 5: Promote to Production."""
    from demo.chapters.chapter_5_promote_production import run

    run()


def run_chapter_6():
    """Chapter 6: Run Batch Inference."""
    from demo.chapters.chapter_6_batch_inference import run

    run()


CHAPTER_RUNNERS = {
    1: run_chapter_1,
    2: run_chapter_2,
    3: run_chapter_3,
    4: run_chapter_4,
    5: run_chapter_5,
    6: run_chapter_6,
}


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
def main(chapter: int, list_chapters: bool, auto: bool):
    """Run the Enterprise MLOps demo."""
    if list_chapters:
        print("\n📚 Demo Chapters:\n")
        for num, (title, _) in CHAPTERS.items():
            print(f"   {num}. {title}")
        print("\nRun with: python demo/run_demo.py --chapter <num>\n")
        return

    print_banner()

    if chapter:
        # Run specific chapter
        if chapter not in CHAPTERS:
            print(f"❌ Invalid chapter: {chapter}. Choose 1-{len(CHAPTERS)}")
            return
        title, _ = CHAPTERS[chapter]
        print_chapter_header(chapter, title)
        CHAPTER_RUNNERS[chapter]()
    else:
        # Run all chapters
        print("This demo walks through the complete model lifecycle.\n")
        print("📚 Chapters:")
        for num, (title, _) in CHAPTERS.items():
            print(f"   {num}. {title}")

        if not auto:
            wait_for_continue()

        for num in sorted(CHAPTERS.keys()):
            title, _ = CHAPTERS[num]
            print_chapter_header(num, title)
            CHAPTER_RUNNERS[num]()

            if not auto and num < len(CHAPTERS):
                wait_for_continue()

    print("\n" + "=" * 75)
    print("  ✅ DEMO COMPLETE")
    print("=" * 75)
    print("\n🔗 Next steps:")
    print("   - View dashboard: zenml up")
    print("   - Run champion/challenger: python run.py --pipeline champion_challenger")
    print("   - See docs: docs/ARCHITECTURE.md")
    print()


if __name__ == "__main__":
    main()
