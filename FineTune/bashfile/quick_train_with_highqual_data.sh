#!/bin/bash
salloc -C "gpu&hbm40g" -q interactive -t 01:00:00 -A m2616_g --gpus 1 srun --pty bash -lc '
echo "================================================================================"
echo "CGSim Fine Tuning with High Quality Data Sets"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started: $(date)"
echo "================================================================================"

cd $HOME/CGSimFinetune

mkdir -p $PSCRATCH/.hf
unset SSL_CERT_FILE REQUESTS_CA_BUNDLE CURL_CA_BUNDLE
export HF_HOME=$PSCRATCH/.hf
export HF_HUB_CACHE=$PSCRATCH/.hf/hub

if [ -n "${SLURM_STEP_GPUS:-}" ]; then
    GPU_SLOT="$(echo "${SLURM_STEP_GPUS}" | cut -d, -f1)"
    export CUDA_VISIBLE_DEVICES="${GPU_SLOT}"
else
    export CUDA_VISIBLE_DEVICES="$(echo "${CUDA_VISIBLE_DEVICES:-0}" | cut -d, -f1)"
fi
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
echo ""

echo "Launching single-GPU training..."
echo "================================================================================"
echo ""

shifter \
    --image=docker:pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime \
    --module=gpu \
    --env HF_HOME=$HF_HOME \
    --env HF_HUB_CACHE=$HF_HUB_CACHE \
    --env CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES \
    --volume "$PSCRATCH:/scratch" \
    --volume "$HOME/CGSimFinetune:/workspace" \
    bash -lc "
        set -euo pipefail
        cd /workspace

        unset SSL_CERT_FILE
        unset REQUESTS_CA_BUNDLE
        unset CURL_CA_BUNDLE

        echo \"Installing required packages...\"
        pip install --no-cache-dir -r  requirements.txt

        echo \"Start Training\"
        python -m FineTune.script.CGSimFineTune_HighQualData
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
'