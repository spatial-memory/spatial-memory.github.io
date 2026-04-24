#!/usr/bin/env python3
"""
GPU Memory Profiler for SLAM Systems
=====================================
Wraps a SLAM process, samples nvidia-smi at regular intervals,
and outputs:
  - CSV time series: timestamp, gpu_mem_MB, cpu_rss_MB
  - Summary: M_peak (GPU), M_peak (CPU), duration
  - Final map size on disk (you provide the path after the run)

Usage:
  # Profile any SLAM command:
  python profile_memory.py --cmd "python run_splatam.py configs/replica/room0.yaml" \
                           --output results/splatam_room0.csv \
                           --interval 1.0 \
                           --gpu-id 0

  # After the run, compute alpha:
  python profile_memory.py --summarize results/splatam_room0.csv --map-size-mb 85

Designed for DGX / multi-GPU systems. Specify --gpu-id to isolate.
"""

import argparse
import csv
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def get_gpu_memory_mb(gpu_id: int) -> float:
    """Query nvidia-smi for current GPU memory usage in MB."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                f"--id={gpu_id}",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return float(result.stdout.strip())
    except Exception:
        return -1.0


def get_cpu_rss_mb(pid: int) -> float:
    """Get RSS of a process in MB via /proc on Linux."""
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0  # kB -> MB
    except Exception:
        pass
    return -1.0


def get_gpu_baseline_mb(gpu_id: int, samples: int = 5, interval: float = 0.5) -> float:
    """Measure baseline GPU memory before launching the SLAM process."""
    readings = []
    for _ in range(samples):
        mem = get_gpu_memory_mb(gpu_id)
        if mem >= 0:
            readings.append(mem)
        time.sleep(interval)
    return sum(readings) / len(readings) if readings else 0.0


def profile_command(cmd: str, output_csv: str, gpu_id: int, interval: float):
    """Launch a command and profile its GPU/CPU memory over time."""
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Measure baseline GPU memory
    print(f"[profiler] Measuring GPU {gpu_id} baseline...")
    baseline_gpu = get_gpu_baseline_mb(gpu_id)
    print(f"[profiler] Baseline GPU memory: {baseline_gpu:.0f} MB")

    # Launch the SLAM process
    print(f"[profiler] Launching: {cmd}")
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    proc = subprocess.Popen(
        cmd, shell=True, env=env, preexec_fn=os.setsid
    )
    pid = proc.pid
    print(f"[profiler] PID={pid}, sampling every {interval}s")

    rows = []
    t_start = time.time()
    peak_gpu = 0.0
    peak_cpu = 0.0

    # Handle Ctrl+C gracefully
    def sigint_handler(sig, frame):
        print("\n[profiler] Interrupted — killing process and saving data...")
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait()
        write_results(output_path, rows, baseline_gpu, peak_gpu, peak_cpu, t_start)
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    try:
        while proc.poll() is None:
            t_now = time.time() - t_start
            gpu_mem = get_gpu_memory_mb(gpu_id)
            cpu_rss = get_cpu_rss_mb(pid)

            # Subtract baseline to get process-attributable GPU memory
            gpu_process = max(0, gpu_mem - baseline_gpu) if gpu_mem >= 0 else -1

            if gpu_mem > peak_gpu:
                peak_gpu = gpu_mem
            if cpu_rss > peak_cpu:
                peak_cpu = cpu_rss

            rows.append({
                "time_s": round(t_now, 2),
                "gpu_total_MB": round(gpu_mem, 1),
                "gpu_process_MB": round(gpu_process, 1),
                "cpu_rss_MB": round(cpu_rss, 1),
            })
            time.sleep(interval)
    except Exception as e:
        print(f"[profiler] Error during profiling: {e}")
    finally:
        proc.wait()

    exit_code = proc.returncode
    print(f"[profiler] Process exited with code {exit_code}")

    write_results(output_path, rows, baseline_gpu, peak_gpu, peak_cpu, t_start)


def write_results(output_path, rows, baseline_gpu, peak_gpu, peak_cpu, t_start):
    """Write CSV and print summary."""
    duration = time.time() - t_start

    # Write CSV
    if rows:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"[profiler] Wrote {len(rows)} samples to {output_path}")

    # Write summary
    summary_path = output_path.with_suffix(".summary.txt")
    summary_lines = [
        f"duration_s: {duration:.1f}",
        f"gpu_baseline_MB: {baseline_gpu:.0f}",
        f"gpu_peak_total_MB: {peak_gpu:.0f}",
        f"gpu_peak_process_MB: {max(0, peak_gpu - baseline_gpu):.0f}",
        f"cpu_peak_rss_MB: {peak_cpu:.0f}",
        f"samples: {len(rows)}",
    ]
    with open(summary_path, "w") as f:
        f.write("\n".join(summary_lines) + "\n")
    print(f"[profiler] Summary written to {summary_path}")
    print()
    for line in summary_lines:
        print(f"  {line}")
    print()
    print("  To compute alpha, run:")
    print(f"  python profile_memory.py --summarize {output_path} --map-size-mb <MAP_MB>")


def summarize(csv_path: str, map_size_mb: float):
    """Read a profiling CSV and compute alpha + print stats."""
    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        print("No data in CSV.")
        return

    gpu_values = [float(r["gpu_process_MB"]) for r in rows if float(r["gpu_process_MB"]) >= 0]
    cpu_values = [float(r["cpu_rss_MB"]) for r in rows if float(r["cpu_rss_MB"]) >= 0]

    gpu_peak = max(gpu_values) if gpu_values else 0
    cpu_peak = max(cpu_values) if cpu_values else 0
    duration = float(rows[-1]["time_s"]) - float(rows[0]["time_s"])

    alpha_gpu = gpu_peak / map_size_mb if map_size_mb > 0 else float("inf")

    print(f"  CSV:            {csv_path}")
    print(f"  Duration:       {duration:.0f} s")
    print(f"  GPU peak:       {gpu_peak:.0f} MB  (process-attributable)")
    print(f"  CPU RSS peak:   {cpu_peak:.0f} MB")
    print(f"  M_map:          {map_size_mb:.0f} MB")
    print(f"  alpha (GPU):    {alpha_gpu:.1f}")
    print()

    # Also compute memory at 25%, 50%, 75% of the run (for M(t) reporting)
    n = len(rows)
    for pct in [25, 50, 75, 100]:
        idx = min(int(n * pct / 100) - 1, n - 1)
        t = float(rows[idx]["time_s"])
        g = float(rows[idx]["gpu_process_MB"])
        print(f"  t={pct}%  ({t:.0f}s):  GPU={g:.0f} MB")


def main():
    parser = argparse.ArgumentParser(description="GPU Memory Profiler for SLAM Systems")
    parser.add_argument("--cmd", type=str, help="Command to profile")
    parser.add_argument("--output", type=str, default="profile_output.csv",
                        help="Output CSV path")
    parser.add_argument("--gpu-id", type=int, default=0, help="GPU ID to monitor")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Sampling interval in seconds")
    parser.add_argument("--summarize", type=str,
                        help="Path to existing CSV to summarize (no profiling)")
    parser.add_argument("--map-size-mb", type=float, default=0,
                        help="Map size on disk in MB (for alpha computation)")
    args = parser.parse_args()

    if args.summarize:
        if args.map_size_mb <= 0:
            print("Error: --map-size-mb required for --summarize")
            sys.exit(1)
        summarize(args.summarize, args.map_size_mb)
    elif args.cmd:
        profile_command(args.cmd, args.output, args.gpu_id, args.interval)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
