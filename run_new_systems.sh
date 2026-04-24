#!/bin/bash
# =============================================================================
# One-shot script: clone, setup, and profile MonoGS, GS-SLAM, SGS-SLAM
#
# Usage (on DGX):
#   bash run_new_systems.sh
#
# Prerequisites:
#   - conda available
#   - Replica dataset at ~/data/Replica/ (from previous profiling)
#   - profile_memory.py in the same directory as this script
# =============================================================================

set -euo pipefail

GPU_ID="${GPU_ID:-0}"
REPLICA_DIR="${REPLICA_DIR:-/data/memory/data}"
REPOS_DIR="${REPOS_DIR:-/data/memory/repos}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROFILER="$SCRIPT_DIR/profile_memory.py"
RESULTS_DIR="$SCRIPT_DIR/results"
SCENE="room0"
INTERVAL=1.0

mkdir -p "$REPOS_DIR" "$RESULTS_DIR"

# Check prerequisites
if [ ! -f "$PROFILER" ]; then
    echo "ERROR: profile_memory.py not found at $PROFILER"
    exit 1
fi
if [ ! -d "$REPLICA_DIR/$SCENE" ]; then
    echo "ERROR: Replica dataset not found at $REPLICA_DIR/$SCENE"
    echo "Download it first: wget https://cvg-data.inf.ethz.ch/nice-slam/data/Replica.zip"
    exit 1
fi

echo "============================================"
echo "New 3DGS System Profiling"
echo "GPU: $GPU_ID | Scene: $SCENE"
echo "Replica: $REPLICA_DIR"
echo "Results: $RESULTS_DIR"
echo "============================================"

# ==========================================================
# 1. MonoGS (highest priority — verifies α ≈ 50 estimate)
# ==========================================================
MONOGS_CSV="$RESULTS_DIR/monogs_${SCENE}.csv"
if [ -f "$MONOGS_CSV" ]; then
    echo ""
    echo ">>> SKIP MonoGS: $MONOGS_CSV already exists"
else
    echo ""
    echo ">>> [1/3] Setting up MonoGS ..."

    cd "$REPOS_DIR"
    if [ ! -d "MonoGS" ]; then
        git clone --recursive https://github.com/muskie82/MonoGS.git
    fi
    cd MonoGS

    # Create conda env if it doesn't exist
    if ! conda env list | grep -q "monogs"; then
        conda create -n monogs python=3.10 -y
    fi

    # Install deps inside a subshell to avoid conda activate issues
    eval "$(conda shell.bash hook)"
    conda activate monogs
    pip install -q -r requirements.txt
    if [ -d "submodules/diff-gaussian-rasterization" ]; then
        pip install -q submodules/diff-gaussian-rasterization
    fi
    if [ -d "submodules/simple-knn" ]; then
        pip install -q submodules/simple-knn
    fi

    # Find the right config — check common locations
    CONFIG=""
    for candidate in \
        "configs/replica/room0.yaml" \
        "configs/Replica/room0.yaml" \
        "configs/replica/mono_replica.yaml" \
        "configs/replica/splatam_replica.yaml"; do
        if [ -f "$candidate" ]; then
            CONFIG="$candidate"
            break
        fi
    done

    if [ -z "$CONFIG" ]; then
        echo "WARNING: Could not find Replica config. Available configs:"
        find configs/ -name "*.yaml" -o -name "*.yml" 2>/dev/null | head -20
        echo "Please set CONFIG manually and re-run the MonoGS section."
    else
        echo "Using config: $CONFIG"

        # Find the right entry point
        ENTRY=""
        for candidate in "slam.py" "run.py" "train.py" "scripts/slam.py"; do
            if [ -f "$candidate" ]; then
                ENTRY="$candidate"
                break
            fi
        done

        if [ -z "$ENTRY" ]; then
            echo "WARNING: Could not find entry point. Available .py files:"
            ls *.py 2>/dev/null
            echo "Please set ENTRY manually."
        else
            echo "Using entry point: $ENTRY"
            echo ">>> Profiling MonoGS on Replica/$SCENE ..."

            python "$PROFILER" \
                --cmd "python $ENTRY $CONFIG" \
                --output "$MONOGS_CSV" \
                --gpu-id "$GPU_ID" \
                --interval "$INTERVAL"

            # Measure map size — check common output locations
            MAP_MB=0
            for map_dir in "output/Replica/$SCENE" "output/$SCENE" "results/$SCENE" "output"; do
                if [ -d "$map_dir" ]; then
                    MAP_MB=$(du -sm "$map_dir" 2>/dev/null | awk '{print $1}')
                    echo "MonoGS map dir: $map_dir ($MAP_MB MB)"
                    break
                fi
            done
            if [ "$MAP_MB" -gt 0 ]; then
                python "$PROFILER" --summarize "$MONOGS_CSV" --map-size-mb "$MAP_MB"
            else
                echo "Map dir not auto-detected. After locating it, run:"
                echo "  python $PROFILER --summarize $MONOGS_CSV --map-size-mb <MAP_MB>"
            fi
        fi
    fi
    conda deactivate
fi

# ==========================================================
# 2. GS-SLAM
# ==========================================================
GSSLAM_CSV="$RESULTS_DIR/gsslam_${SCENE}.csv"
if [ -f "$GSSLAM_CSV" ]; then
    echo ""
    echo ">>> SKIP GS-SLAM: $GSSLAM_CSV already exists"
else
    echo ""
    echo ">>> [2/3] Setting up GS-SLAM ..."

    cd "$REPOS_DIR"
    if [ ! -d "GS-SLAM" ]; then
        # Try the most likely repo URL; adjust if needed
        git clone --recursive https://github.com/muskie82/GS-SLAM.git || \
        echo "WARNING: GS-SLAM clone failed. Check the correct repo URL and clone manually to ~/repos/GS-SLAM"
    fi

    if [ -d "GS-SLAM" ]; then
        cd GS-SLAM

        if ! conda env list | grep -q "gsslam"; then
            conda create -n gsslam python=3.10 -y
        fi

        eval "$(conda shell.bash hook)"
        conda activate gsslam
        pip install -q -r requirements.txt 2>/dev/null || true
        if [ -d "submodules/diff-gaussian-rasterization" ]; then
            pip install -q submodules/diff-gaussian-rasterization
        fi

        CONFIG=""
        for candidate in \
            "configs/replica/${SCENE}.yaml" \
            "configs/Replica/${SCENE}.yaml" \
            "configs/replica/replica.yaml"; do
            if [ -f "$candidate" ]; then
                CONFIG="$candidate"
                break
            fi
        done

        ENTRY=""
        for candidate in "slam.py" "run.py" "train.py"; do
            if [ -f "$candidate" ]; then
                ENTRY="$candidate"
                break
            fi
        done

        if [ -n "$CONFIG" ] && [ -n "$ENTRY" ]; then
            echo "Using: $ENTRY $CONFIG"
            echo ">>> Profiling GS-SLAM on Replica/$SCENE ..."

            python "$PROFILER" \
                --cmd "python $ENTRY $CONFIG" \
                --output "$GSSLAM_CSV" \
                --gpu-id "$GPU_ID" \
                --interval "$INTERVAL"

            for map_dir in "output/Replica/$SCENE" "output/$SCENE" "results/$SCENE"; do
                if [ -d "$map_dir" ]; then
                    MAP_MB=$(du -sm "$map_dir" 2>/dev/null | awk '{print $1}')
                    echo "GS-SLAM map dir: $map_dir ($MAP_MB MB)"
                    python "$PROFILER" --summarize "$GSSLAM_CSV" --map-size-mb "$MAP_MB"
                    break
                fi
            done
        else
            echo "WARNING: Could not find config ($CONFIG) or entry point ($ENTRY)"
            echo "Available configs:"; find configs/ -name "*.yaml" 2>/dev/null | head -10
            echo "Available .py:"; ls *.py 2>/dev/null
        fi
        conda deactivate
    fi
fi

# ==========================================================
# 3. SGS-SLAM
# ==========================================================
SGSSLAM_CSV="$RESULTS_DIR/sgsslam_${SCENE}.csv"
if [ -f "$SGSSLAM_CSV" ]; then
    echo ""
    echo ">>> SKIP SGS-SLAM: $SGSSLAM_CSV already exists"
else
    echo ""
    echo ">>> [3/3] Setting up SGS-SLAM ..."

    cd "$REPOS_DIR"
    if [ ! -d "SGS-SLAM" ]; then
        git clone --recursive https://github.com/IRMVLab/SGS-SLAM.git || \
        echo "WARNING: SGS-SLAM clone failed. Check the correct repo URL and clone manually to ~/repos/SGS-SLAM"
    fi

    if [ -d "SGS-SLAM" ]; then
        cd SGS-SLAM

        if ! conda env list | grep -q "sgsslam"; then
            conda create -n sgsslam python=3.10 -y
        fi

        eval "$(conda shell.bash hook)"
        conda activate sgsslam
        pip install -q -r requirements.txt 2>/dev/null || true
        if [ -d "submodules/diff-gaussian-rasterization" ]; then
            pip install -q submodules/diff-gaussian-rasterization
        fi
        if [ -d "submodules/simple-knn" ]; then
            pip install -q submodules/simple-knn
        fi

        CONFIG=""
        for candidate in \
            "configs/replica/${SCENE}.yaml" \
            "configs/Replica/${SCENE}.yaml" \
            "configs/replica/replica.yaml"; do
            if [ -f "$candidate" ]; then
                CONFIG="$candidate"
                break
            fi
        done

        ENTRY=""
        for candidate in "slam.py" "run.py" "train.py"; do
            if [ -f "$candidate" ]; then
                ENTRY="$candidate"
                break
            fi
        done

        if [ -n "$CONFIG" ] && [ -n "$ENTRY" ]; then
            echo "Using: $ENTRY $CONFIG"
            echo ">>> Profiling SGS-SLAM on Replica/$SCENE ..."

            python "$PROFILER" \
                --cmd "python $ENTRY $CONFIG" \
                --output "$SGSSLAM_CSV" \
                --gpu-id "$GPU_ID" \
                --interval "$INTERVAL"

            for map_dir in "output/Replica/$SCENE" "output/$SCENE" "results/$SCENE"; do
                if [ -d "$map_dir" ]; then
                    MAP_MB=$(du -sm "$map_dir" 2>/dev/null | awk '{print $1}')
                    echo "SGS-SLAM map dir: $map_dir ($MAP_MB MB)"
                    python "$PROFILER" --summarize "$SGSSLAM_CSV" --map-size-mb "$MAP_MB"
                    break
                fi
            done
        else
            echo "WARNING: Could not find config ($CONFIG) or entry point ($ENTRY)"
            echo "Available configs:"; find configs/ -name "*.yaml" 2>/dev/null | head -10
            echo "Available .py:"; ls *.py 2>/dev/null
        fi
        conda deactivate
    fi
fi

# ==========================================================
# Summary
# ==========================================================
echo ""
echo "============================================"
echo "Done. Results:"
for sys in monogs gsslam sgsslam; do
    f="$RESULTS_DIR/${sys}_${SCENE}.csv"
    if [ -f "$f" ]; then
        echo "  [OK] $f"
    else
        echo "  [MISSING] $f"
    fi
done
echo ""
echo "Next: regenerate the M(t) plot:"
echo "  python $SCRIPT_DIR/plot_memory_timeseries.py --results-dir $RESULTS_DIR"
echo "============================================"
