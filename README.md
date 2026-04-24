<div align="center">

# A Survey of Spatial Memory Representations for Efficient Robot Navigation

### Overhead Factor Analysis and Independent Profiling of Neural SLAM Systems

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CVPR 2026](https://img.shields.io/badge/CVPR%202026-WiCV%20Workshop-8A1538.svg)](https://sites.google.com/view/wicv-cvpr-2026/)
[![arXiv](https://img.shields.io/badge/arXiv-2604.16482-b31b1b.svg)](http://arxiv.org/abs/2604.16482)
[![Project Page](https://img.shields.io/badge/project-page-D4A843.svg)](https://memory-eee.github.io/spatial-memory-survey/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

**TL;DR** &mdash; A survey of 88 references spanning 52 systems (1989&ndash;2025) revealing that published map sizes are unreliable proxies for deployment cost. We introduce the **overhead factor &alpha; = M<sub>peak</sub> / M<sub>map</sub>**, independently profile 5 neural SLAM systems on an NVIDIA A100 GPU, and show that &alpha; spans **two orders of magnitude** (2.3&ndash;215) within neural methods alone. A system saving an 8 MB map (Co-SLAM) requires 1.3 GB at runtime (&alpha; = 157).

## Why This Matters

Autonomous robots, drones, and AR headsets operate on embedded GPUs with 8&ndash;16 GB shared memory under strict power budgets (<30 W). Upgrading hardware on a deployed robot is not feasible. SplaTAM (&alpha;<sub>GPU</sub> = 55) consuming 14 GB at runtime leaves <2 GB for perception, planning, and the OS &mdash; making the system infeasible despite the map being only 254 MB. Scaling to a 100 m&sup2; apartment would extrapolate to ~200 GB, far exceeding even a data-center-class A100 (80 GB). **Memory efficiency is a feasibility constraint, not a cost problem.**

## Key Results

### Overhead Factor &alpha; Across Profiled Systems

| System | Paradigm | ATE (cm) | PSNR (dB) | Map (MB) | Peak (MB) | FPS | &alpha; |
|--------|----------|:--------:|:---------:|:--------:|:---------:|:---:|:-------:|
| | **Sparse &mdash; EuRoC (real-world)** | | | | | | |
| ORB-SLAM3 | Sparse | 3.5 | &mdash; | 55 | 220 | 30 | **4.0** |
| Basalt | Sparse (VI) | 8.8 | &mdash; | 35 | 120 | 30 | **~3.4** |
| | **Neural &mdash; Replica (synthetic)** | | | | | | |
| Point-SLAM | NeRF | 0.52 | 35.2 | 2,865 | 6,563 | 1 | **2.3** |
| SplaTAM | 3DGS | 0.36 | 34.1 | 254 | 14,024 | &mdash; | **55** |
| Co-SLAM | NeRF | 1.00 | 30.2 | 8 | 1,258 | 16 | **157** |
| SGS-SLAM | 3DGS (Sem.) | 0.41 | 34.7 | 254 | 40,330 | 2 | **159** |
| NICE-SLAM | NeRF | 1.06 | 24.4 | 47 | 10,082 | 2 | **215** |

<sub>&alpha;<sub>CPU</sub> (CPU RSS) for sparse systems (Intel i7-10700). &alpha;<sub>GPU</sub> (GPU allocation) for neural systems (NVIDIA A100-SXM4-80GB, Replica/room0, 1 Hz sampling, baseline subtracted). ATE = Absolute Trajectory Error (RMSE). PSNR = Peak Signal-to-Noise Ratio.</sub>

### Checkpoint Discrepancies with Literature

| System | Ours (MB) | Literature (MB) | Ratio |
|--------|:---------:|:---------------:|:-----:|
| Co-SLAM | 8 | 32 | 0.25&times; |
| NICE-SLAM | 47 | 235 | 0.20&times; |
| Point-SLAM | 2,865 | 80 | 35.8&times; |
| SplaTAM | 254 | 85 | 3.0&times; |
| SGS-SLAM | 254 | 92 | 2.8&times; |

<sub>Every profiled system showed discrepancies. 3DGS checkpoints are ~3&times; larger because saved Gaussian parameters exceed typically reported counts.</sub>

### Memory Growth Dynamics

| Pattern | System | Behavior |
|---------|--------|----------|
| Bounded | Co-SLAM | Flat at ~1.3 GB (pre-allocated hash table) |
| Oscillating | NICE-SLAM | 3&ndash;7 GB (periodic global mapping passes) |
| Unbounded | SplaTAM | Monotonic growth to ~12.7 GB (no pruning) |
| Stabilizing | Point-SLAM | Settles at ~5.5 GB after initialization |

### &alpha;-Aware Budgeting

**M<sub>map</sub><sup>max</sup> = M<sub>budget</sub> / &alpha;**

| Constraint | Recommended | &alpha; range | Type | Max Map | Avoid |
|------------|-------------|:-------------:|------|---------|-------|
| CPU-only (<8 GB) | Sparse, Octree | 3&ndash;5 | CPU | ~4 GB | Neural |
| Embedded GPU (<16 GB) | Sparse, SG | 4&ndash;10 | CPU | ~2 GB | Raw 3DGS |
| Dense geometry | TSDF, 3DGS | ~55 | GPU | 290 MB | Sparse only |
| Photo rendering | 3DGS, NeRF | 2&ndash;215 | GPU | 75 MB | Occupancy |

<sub>Example: Jetson Orin NX (16 GB) with &alpha;<sub>GPU</sub> &isin; [55, 215]: M<sub>map</sub><sup>max</sup> &asymp; 75&ndash;290 MB. With sparse SLAM (&alpha;<sub>CPU</sub> &asymp; 4): ~4 GB.</sub>

## Repository Structure

```
.
├── profile_memory.py          # GPU/CPU memory profiler — wraps any SLAM command
├── plot_memory_timeseries.py  # Generates M(t) plots (matplotlib PDF + pgfplots CSVs)
├── run_all.sh                 # Profile all 7 systems in sequence
├── run_new_systems.sh         # Clone, setup, and profile MonoGS / GS-SLAM / SGS-SLAM
├── INSTRUCTIONS.md            # Detailed setup guide for each SLAM system on DGX
├── results/                   # Profiling output (CSVs, summaries, logs)
│   ├── coslam_room0.csv
│   ├── niceslam_room0.csv
│   ├── pointslam_room0.csv
│   ├── splatam_room0.csv
│   ├── sgsslam_room0.csv
│   ├── monogs_room0.csv
│   ├── gaussianslam_room0.csv
│   └── *.summary.txt          # Per-system peak memory + duration
└── docs/                      # Project page (GitHub Pages)
    ├── index.html
    └── static/images/
```

## Quick Start

### Prerequisites

- NVIDIA GPU with &ge; 12 GB VRAM
- `nvidia-smi` available
- Conda (for per-system environments)
- Replica dataset ([NICE-SLAM preprocessed version](https://cvg-data.inf.ethz.ch/nice-slam/data/Replica.zip))

### Profile a Single System

```bash
conda activate <system_env>
cd ~/repos/<SystemRepo>

python profile_memory.py \
    --cmd "python <entry_point> <config>" \
    --output results/<system>_room0.csv \
    --gpu-id 0 \
    --interval 1.0
```

### Compute &alpha;

```bash
python profile_memory.py \
    --summarize results/<system>_room0.csv \
    --map-size-mb <MAP_MB>
```

### Generate M(t) Plot

```bash
python plot_memory_timeseries.py --results-dir results/
```

Outputs:
- `results/memory_timeseries.pdf` &mdash; matplotlib preview
- `results/memory_timeseries_data/` &mdash; per-system CSVs for pgfplots
- LaTeX snippet (printed to stdout) for paper inclusion

### Run All Systems

```bash
export GPU_ID=0
export REPLICA_DIR=~/data/Replica
bash run_all.sh          # all 7 systems (requires repos pre-cloned)
bash run_new_systems.sh  # auto-clone + profile MonoGS, GS-SLAM, SGS-SLAM
```

## How It Works

1. **Baseline measurement** &mdash; samples GPU memory before launching the SLAM process
2. **Continuous profiling** &mdash; polls `nvidia-smi` at a configurable interval while the SLAM process runs
3. **Summary** &mdash; reports peak GPU/CPU memory, duration, and computes &alpha; = M<sub>peak</sub> / M<sub>map</sub>

See [INSTRUCTIONS.md](INSTRUCTIONS.md) for detailed per-system setup and troubleshooting.

## Citation

```bibtex
@inproceedings{pangaliman2026survey,
  title     = {A Survey of Spatial Memory Representations for Efficient Robot Navigation},
  author    = {Pangaliman, Ma. Madecheen S. and Sison, Steven S. and Quilloy, Erwin P. and Atienza, Rowel},
  booktitle = {IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) Workshops},
  year      = {2026}
}
```

## Acknowledgements

The authors would like to thank the Engineering Research and Development for Technology (ERDT) program of the Department of Science and Technology &ndash; Science Education Institute (DOST-SEI), Philippines, the Office of International Linkages (OIL) of the University of the Philippines Diliman, and the Research Dissemination Grant of the UP Artificial Intelligence Research Program for supporting this work. We are also grateful to the Ubiquitous Computing Laboratory at UP Diliman for providing computational resources.
