#!/usr/bin/env python3
"""
Plot M(t) memory time series from profiling CSVs.
Generates a PGF/TikZ-compatible CSV + a quick matplotlib preview.

Usage:
  python plot_memory_timeseries.py --results-dir results/
  python plot_memory_timeseries.py --csvs results/splatam_room0.csv results/niceslam_room0.csv

Output:
  - results/memory_timeseries.pdf   (matplotlib preview)
  - results/memory_timeseries_data/  (per-system CSVs for pgfplots)
"""

import argparse
import csv
import os
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("WARNING: matplotlib not found — skipping PDF plot, writing CSVs only.")


SYSTEM_LABELS = {
    "splatam": "SplaTAM",
    "niceslam": "NICE-SLAM",
    "pointslam": "Point-SLAM",
    "coslam": "Co-SLAM",
    "monogs": "MonoGS",
    "gsslam": "GS-SLAM",
    "sgsslam": "SGS-SLAM",
}

SYSTEM_COLORS = {
    "splatam": "#e67e22",
    "niceslam": "#c0392b",
    "pointslam": "#8e44ad",
    "coslam": "#2980b9",
    "monogs": "#27ae60",
    "gsslam": "#f39c12",
    "sgsslam": "#16a085",
}


def load_csv(path):
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "time_s": float(row["time_s"]),
                "gpu_MB": float(row["gpu_process_MB"]),
            })
    return rows


def normalize_time_pct(rows):
    """Normalize time to 0-100% of run duration."""
    if not rows:
        return rows
    t_max = rows[-1]["time_s"]
    if t_max == 0:
        return rows
    for r in rows:
        r["time_pct"] = 100.0 * r["time_s"] / t_max
    return rows


def downsample(rows, max_points=200):
    """Downsample for clean plotting."""
    if len(rows) <= max_points:
        return rows
    step = len(rows) // max_points
    return rows[::step] + [rows[-1]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=str, default="results/")
    parser.add_argument("--csvs", nargs="+", type=str, default=None)
    parser.add_argument("--time-axis", choices=["seconds", "percent"], default="percent",
                        help="X-axis: absolute seconds or normalized percent")
    args = parser.parse_args()

    # Find CSVs
    if args.csvs:
        csv_files = [Path(p) for p in args.csvs]
    else:
        csv_files = sorted(Path(args.results_dir).glob("*.csv"))
        # Exclude summary files
        csv_files = [f for f in csv_files if ".summary" not in f.name]

    if not csv_files:
        print(f"No CSV files found in {args.results_dir}")
        return

    # Load all systems
    systems = {}
    for f in csv_files:
        # Extract system name from filename (e.g., splatam_room0.csv -> splatam)
        name = f.stem.split("_")[0]
        rows = load_csv(f)
        if args.time_axis == "percent":
            rows = normalize_time_pct(rows)
        rows = downsample(rows)
        systems[name] = rows
        print(f"  Loaded {name}: {len(rows)} points, peak={max(r['gpu_MB'] for r in rows):.0f} MB")

    # Write per-system CSVs for pgfplots
    pgf_dir = Path(args.results_dir) / "memory_timeseries_data"
    pgf_dir.mkdir(parents=True, exist_ok=True)

    for name, rows in systems.items():
        out_path = pgf_dir / f"{name}.csv"
        with open(out_path, "w", newline="") as f:
            writer = csv.writer(f)
            if args.time_axis == "percent":
                writer.writerow(["time_pct", "gpu_MB"])
                for r in rows:
                    writer.writerow([f"{r['time_pct']:.1f}", f"{r['gpu_MB']:.0f}"])
            else:
                writer.writerow(["time_s", "gpu_MB"])
                for r in rows:
                    writer.writerow([f"{r['time_s']:.1f}", f"{r['gpu_MB']:.0f}"])
        print(f"  Wrote pgfplots data: {out_path}")

    # Matplotlib preview
    if HAS_MPL:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        for name, rows in systems.items():
            label = SYSTEM_LABELS.get(name, name)
            color = SYSTEM_COLORS.get(name, None)
            if args.time_axis == "percent":
                x = [r["time_pct"] for r in rows]
                ax.set_xlabel("Run Progress (%)")
            else:
                x = [r["time_s"] for r in rows]
                ax.set_xlabel("Time (s)")
            y = [r["gpu_MB"] for r in rows]
            ax.plot(x, y, label=label, color=color, linewidth=1.5)

        ax.set_ylabel("GPU Memory (MB)")
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(True, alpha=0.3)
        ax.set_title("Runtime Memory Growth on Replica/room0")

        out_pdf = Path(args.results_dir) / "memory_timeseries.pdf"
        fig.tight_layout()
        fig.savefig(out_pdf, dpi=150)
        print(f"  Wrote plot: {out_pdf}")
        plt.close()

    # Print pgfplots snippet for inclusion in LaTeX
    print()
    print("=== pgfplots LaTeX snippet (paste into main.tex) ===")
    print()
    xlabel = "Run Progress (\\%)" if args.time_axis == "percent" else "Time (s)"
    xcol = "time_pct" if args.time_axis == "percent" else "time_s"
    print(r"\begin{figure}[t]")
    print(r"\centering")
    print(r"\begin{tikzpicture}")
    print(r"\begin{axis}[")
    print(f"    xlabel={{{xlabel}}},")
    print(r"    ylabel={GPU Memory (MB)},")
    print(r"    grid=major, grid style={gray!20},")
    print(r"    width=\columnwidth, height=5cm,")
    print(r"    legend style={at={(0.03,0.97)}, anchor=north west, font=\scriptsize},")
    print(r"]")
    for name in systems:
        label = SYSTEM_LABELS.get(name, name)
        color = {"splatam": "orange", "niceslam": "red!70!black",
                 "pointslam": "purple!70!black", "coslam": "blue!70!black",
                 "monogs": "green!60!black", "gsslam": "yellow!70!black",
                 "sgsslam": "teal"}.get(name, "black")
        print(f"\\addplot[{color}, thick] table[x={xcol}, y=gpu_MB, col sep=comma]")
        print(f"    {{memory_timeseries_data/{name}.csv}};")
        print(f"\\addlegendentry{{{label}}}")
    print(r"\end{axis}")
    print(r"\end{tikzpicture}")
    print(r"\caption{Runtime GPU memory over time on Replica/room0. ...}")
    print(r"\label{fig:memory_growth}")
    print(r"\end{figure}")


if __name__ == "__main__":
    main()
