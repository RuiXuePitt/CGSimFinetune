#!/bin/bash
#SBATCH --job-name=cgsim-train-highqual-data
#SBATCH --account=m2616_g
#SBATCH --constraint=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --qos=regular
#SBATCH --time=01:00:00
#SBATCH --output=logs/slurm-cgsim-train-highqual-data-%j.out
#SBATCH --image=docker:pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime
#SBATCH --module=gpu

# exit when encountered fails
set -euo pipefail
echo "================================================================================"
echo "CGSim Fine Tuning with High Quality Data Sets"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started: $(date)"
echo "================================================================================"

cd $HOME/CGSimFinetune

mkdir -p $PSCRATCH/.hf

# unset dead paths (?)
unset SSL_CERT_FILE
unset REQUESTS_CA_BUNDLE
unset CURL_CA_BUNDLE

export HF_HOME=$PSCRATCH/.hf
export HF_HUB_CACHE=$PSCRATCH/.hf/hub
export TRANSFORMERS_CACHE=$PSCRATCH/.hf/transformers
export HF_DATASETS_CACHE=$PSCRATCH/.hf/datasets
export PATH=$HOME/.local/bin:$PATH

# GPU information
echo "GPU Information:"
nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader
echo ""

# Enforce single-GPU visibility inside and outside the container.
# Prefer Slurm-assigned GPU list when available.
if [ -n "${SLURM_STEP_GPUS:-}" ]; then
    GPU_SLOT="$(echo "${SLURM_STEP_GPUS}" | cut -d',' -f1)"
    export CUDA_VISIBLE_DEVICES="${GPU_SLOT}"
else
    export CUDA_VISIBLE_DEVICES="$(echo "${CUDA_VISIBLE_DEVICES:-0}" | cut -d',' -f1)"
fi
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
echo ""

echo "Launching single-GPU training..."
echo "================================================================================"
echo ""

srun shifter \
    --image=docker:pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime \
    --module=gpu \
    --env HF_HOME=$HF_HOME \
    --env HF_HUB_CACHE=$HF_HUB_CACHE \
    --env TRANSFORMERS_CACHE=$TRANSFORMERS_CACHE \
    --env HF_DATASETS_CACHE=$HF_DATASETS_CACHE \
    --env CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES \
    --volume "$PSCRATCH:/scratch" \
    --volume "$PWD:/workspace" \
    bash -lc "
        set -euo pipefail
        cd /workspace

        unset SSL_CERT_FILE
        unset REQUESTS_CA_BUNDLE
        unset CURL_CA_BUNDLE

        echo 'Installing required packages...'
        pip install --no-cache-dir -r  requirements.txt

        echo 'Start Training'
        python FineTune/CGSimFineTune_HighQualData.py
    "

EXIT_CODE=$?

echo ""
echo "================================================================================"
echo "Training completed with exit code: $EXIT_CODE"
echo "Ended: $(date)"
echo "================================================================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Training succeeded!"
else
    echo "❌ Training failed!"
fi

exit $EXIT_CODE