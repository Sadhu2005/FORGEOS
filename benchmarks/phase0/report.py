"""Render the latest Phase 0 benchmark results as a terminal + markdown report.

Usage:
    python -m benchmarks.phase0.report
    python -m benchmarks.phase0.report --input benchmarks/phase0/results/20260101_120000.json
"""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from tabulate import tabulate

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _latest_results_file() -> Path:
    candidates = sorted(RESULTS_DIR.glob("*.json"))
    if not candidates:
        raise SystemExit(
            f"No benchmark results found in {RESULTS_DIR}. "
            "Run `python -m benchmarks.phase0.bench` first."
        )
    return candidates[-1]


def _mean(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else None


def summarize(results: dict) -> dict:
    """Group raw per-run results by model and category, computing means/peaks."""
    summary: dict = {"timestamp": results["timestamp"], "system": results["system"], "models": {}}

    for model, model_data in results["models"].items():
        runs = model_data["runs"]
        categories: dict[str, list[dict]] = {}
        for run in runs:
            categories.setdefault(run["category"], []).append(run)

        ram_deltas = [r["ram_after_mb"] - r["ram_before_mb"] for r in runs]
        vram_deltas = [
            r["vram_after_mb"] - r["vram_before_mb"]
            for r in runs
            if r["vram_after_mb"] is not None and r["vram_before_mb"] is not None
        ]

        per_category = {}
        for category, cat_runs in categories.items():
            per_category[category] = {
                "avg_tokens_per_sec": _mean([r["tokens_per_sec"] for r in cat_runs]),
                "avg_ttft_s": _mean([r["ttft_s"] for r in cat_runs]),
                "avg_total_time_s": _mean([r["total_time_s"] for r in cat_runs]),
            }

        summary["models"][model] = {
            "load_duration_s": model_data["load_duration_s"],
            "overall_avg_tokens_per_sec": _mean([r["tokens_per_sec"] for r in runs]),
            "overall_avg_ttft_s": _mean([r["ttft_s"] for r in runs]),
            "peak_ram_delta_mb": max(ram_deltas) if ram_deltas else None,
            "peak_vram_delta_mb": max(vram_deltas) if vram_deltas else None,
            "avg_cpu_percent": _mean([r["cpu_percent_after"] for r in runs]),
            "categories": per_category,
        }

    return summary


def print_terminal_report(summary: dict) -> None:
    console = Console(width=120)
    console.print(f"\n[bold]FORGEOS Phase 0 Benchmark Report[/bold] - {summary['timestamp']}")
    console.print(
        f"System: CPU={summary['system']['cpu']}  GPU={summary['system']['gpu']}\n"
    )

    overview = Table(title="Overall model comparison")
    overview.add_column("Model", no_wrap=True)
    overview.add_column("Load (s)", justify="right")
    overview.add_column("Avg tok/s", justify="right")
    overview.add_column("Avg TTFT (s)", justify="right")
    overview.add_column("Peak RAM Delta (MB)", justify="right")
    overview.add_column("Peak VRAM Delta (MB)", justify="right")
    overview.add_column("Avg CPU %", justify="right")

    for model, m in summary["models"].items():
        overview.add_row(
            model,
            f"{m['load_duration_s']:.2f}" if m["load_duration_s"] else "n/a",
            f"{m['overall_avg_tokens_per_sec']:.1f}" if m["overall_avg_tokens_per_sec"] else "n/a",
            f"{m['overall_avg_ttft_s']:.2f}" if m["overall_avg_ttft_s"] else "n/a",
            f"{m['peak_ram_delta_mb']:.0f}" if m["peak_ram_delta_mb"] is not None else "n/a",
            f"{m['peak_vram_delta_mb']:.0f}" if m["peak_vram_delta_mb"] is not None else "n/a",
            f"{m['avg_cpu_percent']:.1f}" if m["avg_cpu_percent"] is not None else "n/a",
        )
    console.print(overview)

    for model, m in summary["models"].items():
        cat_table = Table(title=f"{model} - by category")
        cat_table.add_column("Category")
        cat_table.add_column("Avg tok/s", justify="right")
        cat_table.add_column("Avg TTFT (s)", justify="right")
        cat_table.add_column("Avg total time (s)", justify="right")
        for category, c in m["categories"].items():
            cat_table.add_row(
                category,
                f"{c['avg_tokens_per_sec']:.1f}" if c["avg_tokens_per_sec"] else "n/a",
                f"{c['avg_ttft_s']:.2f}" if c["avg_ttft_s"] else "n/a",
                f"{c['avg_total_time_s']:.2f}" if c["avg_total_time_s"] else "n/a",
            )
        console.print(cat_table)


def render_markdown(summary: dict) -> str:
    lines = [
        "# FORGEOS Phase 0 Benchmark Report",
        "",
        f"- Generated: {summary['timestamp']}",
        f"- CPU: {summary['system']['cpu']}",
        f"- GPU: {summary['system']['gpu']}",
        "",
        "## Overall model comparison",
        "",
    ]

    overview_rows = []
    for model, m in summary["models"].items():
        overview_rows.append(
            [
                model,
                f"{m['load_duration_s']:.2f}" if m["load_duration_s"] else "n/a",
                f"{m['overall_avg_tokens_per_sec']:.1f}" if m["overall_avg_tokens_per_sec"] else "n/a",
                f"{m['overall_avg_ttft_s']:.2f}" if m["overall_avg_ttft_s"] else "n/a",
                f"{m['peak_ram_delta_mb']:.0f}" if m["peak_ram_delta_mb"] is not None else "n/a",
                f"{m['peak_vram_delta_mb']:.0f}" if m["peak_vram_delta_mb"] is not None else "n/a",
                f"{m['avg_cpu_percent']:.1f}" if m["avg_cpu_percent"] is not None else "n/a",
            ]
        )
    lines.append(
        tabulate(
            overview_rows,
            headers=["Model", "Load (s)", "Avg tok/s", "Avg TTFT (s)", "Peak RAM Delta (MB)", "Peak VRAM Delta (MB)", "Avg CPU %"],
            tablefmt="github",
        )
    )
    lines.append("")

    for model, m in summary["models"].items():
        lines.append(f"## {model} - by category")
        lines.append("")
        cat_rows = []
        for category, c in m["categories"].items():
            cat_rows.append(
                [
                    category,
                    f"{c['avg_tokens_per_sec']:.1f}" if c["avg_tokens_per_sec"] else "n/a",
                    f"{c['avg_ttft_s']:.2f}" if c["avg_ttft_s"] else "n/a",
                    f"{c['avg_total_time_s']:.2f}" if c["avg_total_time_s"] else "n/a",
                ]
            )
        lines.append(
            tabulate(
                cat_rows,
                headers=["Category", "Avg tok/s", "Avg TTFT (s)", "Avg total time (s)"],
                tablefmt="github",
            )
        )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the latest Phase 0 benchmark results")
    parser.add_argument("--input", type=Path, default=None, help="Specific results JSON to render")
    args = parser.parse_args()

    input_path = args.input or _latest_results_file()
    results = json.loads(input_path.read_text(encoding="utf-8"))
    summary = summarize(results)

    print_terminal_report(summary)

    md = render_markdown(summary)
    out_path = input_path.with_name(input_path.stem + "_report.md")
    out_path.write_text(md, encoding="utf-8")
    print(f"\nMarkdown report written to {out_path}")


if __name__ == "__main__":
    main()
