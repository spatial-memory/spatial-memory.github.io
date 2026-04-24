#!/bin/bash
# =============================================================================
# Master profiling script for SLAM memory measurement
# Run on DGX with one free GPU. Expects repos + Replica already set up
# (see INSTRUCTIONS.md for setup steps).
#
# Usage:
#   export GPU_ID=0          # whichever GPU is free
#   export REPLICA_DIR=/path/to/Replica
#   bash run_all.sh
# =============================================================================

set -euo pipefail

GPU_ID="${GPU_ID:-0}"
REPLICA_DIR="${REPLICA_DIR:-$HOME/data/Replica}"
RESULTS_DIR="$(dirname "$0")/results"
PROFILER="$(dirname "$0")/profile_memory.py"
SCENE="room0"        # Replica scene — consistent across all systems
INTERVAL=1.0         # Sample every 1 second

mkdir -p "$RESULTS_DIR"

echo "============================================"
echo "SLAM Memory Profiling"
echo "GPU: $GPU_ID | Scene: $SCENE | Interval: ${INTERVAL}s"
echo "Results: $RESULTS_DIR"
echo "============================================"

# ---------- 1. SplaTAM ----------
if [ -d "$HOME/repos/SplaTAM" ]; then
    echo ""
    echo ">>> Profiling SplaTAM on Replica/$SCENE ..."
    cd "$HOME/repos/SplaTAM"

    python "$PROFILER" \
        --cmd "python scripts/splatam.py configs/replica/splatam.py" \
        --output "$RESULTS_DIR/splatam_${SCENE}.csv" \
        --gpu-id "$GPU_ID" \
        --interval "$INTERVAL"

    # Map size: find the output directory and measure
    MAP_DIR="experiments/Replica/${SCENE}"
    if [ -d "$MAP_DIR" ]; then
        MAP_MB=$(du -sm "$MAP_DIR"/params*.npz 2>/dev/null | awk '{sum+=$1} END{print sum+0}')
        echo "SplaTAM map size: ${MAP_MB} MB"
        python "$PROFILER" --summarize "$RESULTS_DIR/splatam_${SCENE}.csv" --map-size-mb "$MAP_MB"
    else
        echo "WARNING: SplaTAM output dir not found at $MAP_DIR"
        echo "After locating the map file, run:"
        echo "  python $PROFILER --summarize $RESULTS_DIR/splatam_${SCENE}.csv --map-size-mb <MAP_MB>"
    fi
else
    echo "SKIP: SplaTAM not found at $HOME/repos/SplaTAM"
fi

# ---------- 2. NICE-SLAM ----------
if [ -d "$HOME/repos/NICE-SLAM" ]; then
    echo ""
    echo ">>> Profiling NICE-SLAM on Replica/$SCENE ..."
    cd "$HOME/repos/NICE-SLAM"

    python "$PROFILER" \
        --cmd "python run.py configs/Replica/${SCENE}.yaml" \
        --output "$RESULTS_DIR/niceslam_${SCENE}.csv" \
        --gpu-id "$GPU_ID" \
        --interval "$INTERVAL"

    MAP_DIR="output/Replica/${SCENE}"
    if [ -d "$MAP_DIR" ]; then
        MAP_MB=$(du -sm "$MAP_DIR"/*.pt 2>/dev/null | awk '{sum+=$1} END{print sum+0}')
        echo "NICE-SLAM map size: ${MAP_MB} MB"
        python "$PROFILER" --summarize "$RESULTS_DIR/niceslam_${SCENE}.csv" --map-size-mb "$MAP_MB"
    else
        echo "WARNING: NICE-SLAM output dir not found at $MAP_DIR"
        echo "  python $PROFILER --summarize $RESULTS_DIR/niceslam_${SCENE}.csv --map-size-mb <MAP_MB>"
    fi
else
    echo "SKIP: NICE-SLAM not found at $HOME/repos/NICE-SLAM"
fi

# ---------- 3. Point-SLAM ----------
if [ -d "$HOME/repos/Point-SLAM" ]; then
    echo ""
    echo ">>> Profiling Point-SLAM on Replica/$SCENE ..."
    cd "$HOME/repos/Point-SLAM"

    python "$PROFILER" \
        --cmd "python run.py configs/Replica/${SCENE}.yaml" \
        --output "$RESULTS_DIR/pointslam_${SCENE}.csv" \
        --gpu-id "$GPU_ID" \
        --interval "$INTERVAL"

    MAP_DIR="output/Replica/${SCENE}"
    if [ -d "$MAP_DIR" ]; then
        MAP_MB=$(du -sm "$MAP_DIR"/*.pt 2>/dev/null | awk '{sum+=$1} END{print sum+0}')
        echo "Point-SLAM map size: ${MAP_MB} MB"
        python "$PROFILER" --summarize "$RESULTS_DIR/pointslam_${SCENE}.csv" --map-size-mb "$MAP_MB"
    else
        echo "WARNING: Point-SLAM output dir not found at $MAP_DIR"
        echo "  python $PROFILER --summarize $RESULTS_DIR/pointslam_${SCENE}.csv --map-size-mb <MAP_MB>"
    fi
else
    echo "SKIP: Point-SLAM not found at $HOME/repos/Point-SLAM"
fi

# ---------- 4. MonoGS (NEW — 3DGS, priority) ----------
if [ -d "$HOME/repos/MonoGS" ]; then
    echo ""
    echo ">>> Profiling MonoGS on Replica/$SCENE ..."
    cd "$HOME/repos/MonoGS"

    python "$PROFILER" \
        --cmd "python slam.py configs/replica/room0.yaml" \
        --output "$RESULTS_DIR/monogs_${SCENE}.csv" \
        --gpu-id "$GPU_ID" \
        --interval "$INTERVAL"

    # Map size: MonoGS saves Gaussian params as .ply or .pt
    # Check the output directory structure after the first run
    MAP_DIR="output/Replica/${SCENE}"
    if [ -d "$MAP_DIR" ]; then
        MAP_MB=$(du -sm "$MAP_DIR" 2>/dev/null | awk '{print $1}')
        echo "MonoGS map size: ${MAP_MB} MB"
        python "$PROFILER" --summarize "$RESULTS_DIR/monogs_${SCENE}.csv" --map-size-mb "$MAP_MB"
    else
        echo "WARNING: MonoGS output dir not found at $MAP_DIR"
        echo "  Check README for output path, then run:"
        echo "  python $PROFILER --summarize $RESULTS_DIR/monogs_${SCENE}.csv --map-size-mb <MAP_MB>"
    fi
else
    echo "SKIP: MonoGS not found at $HOME/repos/MonoGS"
fi

# ---------- 5. GS-SLAM (NEW — 3DGS) ----------
if [ -d "$HOME/repos/GS-SLAM" ]; then
    echo ""
    echo ">>> Profiling GS-SLAM on Replica/$SCENE ..."
    cd "$HOME/repos/GS-SLAM"

    python "$PROFILER" \
        --cmd "python slam.py configs/replica/${SCENE}.yaml" \
        --output "$RESULTS_DIR/gsslam_${SCENE}.csv" \
        --gpu-id "$GPU_ID" \
        --interval "$INTERVAL"

    MAP_DIR="output/Replica/${SCENE}"
    if [ -d "$MAP_DIR" ]; then
        MAP_MB=$(du -sm "$MAP_DIR" 2>/dev/null | awk '{print $1}')
        echo "GS-SLAM map size: ${MAP_MB} MB"
        python "$PROFILER" --summarize "$RESULTS_DIR/gsslam_${SCENE}.csv" --map-size-mb "$MAP_MB"
    else
        echo "WARNING: GS-SLAM output dir not found at $MAP_DIR"
        echo "  python $PROFILER --summarize $RESULTS_DIR/gsslam_${SCENE}.csv --map-size-mb <MAP_MB>"
    fi
else
    echo "SKIP: GS-SLAM not found at $HOME/repos/GS-SLAM"
fi

# ---------- 6. SGS-SLAM (NEW — 3DGS) ----------
if [ -d "$HOME/repos/SGS-SLAM" ]; then
    echo ""
    echo ">>> Profiling SGS-SLAM on Replica/$SCENE ..."
    cd "$HOME/repos/SGS-SLAM"

    python "$PROFILER" \
        --cmd "python slam.py configs/replica/${SCENE}.yaml" \
        --output "$RESULTS_DIR/sgsslam_${SCENE}.csv" \
        --gpu-id "$GPU_ID" \
        --interval "$INTERVAL"

    MAP_DIR="output/Replica/${SCENE}"
    if [ -d "$MAP_DIR" ]; then
        MAP_MB=$(du -sm "$MAP_DIR" 2>/dev/null | awk '{print $1}')
        echo "SGS-SLAM map size: ${MAP_MB} MB"
        python "$PROFILER" --summarize "$RESULTS_DIR/sgsslam_${SCENE}.csv" --map-size-mb "$MAP_MB"
    else
        echo "WARNING: SGS-SLAM output dir not found at $MAP_DIR"
        echo "  python $PROFILER --summarize $RESULTS_DIR/sgsslam_${SCENE}.csv --map-size-mb <MAP_MB>"
    fi
else
    echo "SKIP: SGS-SLAM not found at $HOME/repos/SGS-SLAM"
fi

# ---------- 7. Co-SLAM (validation — should match α ≈ 100) ----------
if [ -d "$HOME/repos/Co-SLAM" ]; then
    echo ""
    echo ">>> Profiling Co-SLAM on Replica/$SCENE (validation) ..."
    cd "$HOME/repos/Co-SLAM"

    python "$PROFILER" \
        --cmd "python run.py configs/Replica/${SCENE}.yaml" \
        --output "$RESULTS_DIR/coslam_${SCENE}.csv" \
        --gpu-id "$GPU_ID" \
        --interval "$INTERVAL"

    MAP_DIR="output/Replica/${SCENE}"
    if [ -d "$MAP_DIR" ]; then
        MAP_MB=$(du -sm "$MAP_DIR"/*.pt 2>/dev/null | awk '{sum+=$1} END{print sum+0}')
        echo "Co-SLAM map size: ${MAP_MB} MB"
        python "$PROFILER" --summarize "$RESULTS_DIR/coslam_${SCENE}.csv" --map-size-mb "$MAP_MB"
    else
        echo "  python $PROFILER --summarize $RESULTS_DIR/coslam_${SCENE}.csv --map-size-mb 32"
    fi
else
    echo "SKIP: Co-SLAM not found at $HOME/repos/Co-SLAM"
fi

echo ""
echo "============================================"
echo "All profiling runs complete."
echo "Results in: $RESULTS_DIR/"
echo ""
echo "Next: generate the M(t) plot:"
echo "  python plot_memory_timeseries.py --results-dir $RESULTS_DIR"
echo "============================================"
