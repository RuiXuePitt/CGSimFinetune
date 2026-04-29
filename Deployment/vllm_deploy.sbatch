#!/bin/bash
#SBATCH --job-name=BaseLLM-vllm-server
#SBATCH --account=m2616_g
#SBATCH --constraint=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --qos=regular
#SBATCH --time=01:00:00
#SBATCH --output=logs/slurm-BaseLLM-vllm-%j.out

set -euo pipefail
echo "================================================================================"
echo "Deploy base LLM through vLLM"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started: $(date)"
echo "================================================================================"

cd $HOME/CGSimFinetune
mkdir -p logs $PSCRATCH/.hf

# unset dead paths (?)
unset SSL_CERT_FILE
unset REQUESTS_CA_BUNDLE
unset CURL_CA_BUNDLE

export HF_HOME=$PSCRATCH/.hf
export HF_HUB_CACHE=$PSCRATCH/.hf/hub
export TRANSFORMERS_CACHE=$PSCRATCH/.hf/transformers
export HF_DATASETS_CACHE=$PSCRATCH/.hf/datasets

MODEL_ID="AI4SciNoob/Llama-3.1-Nemotron-Nano-8B-v1-AskCGSim"
SERVED_MODEL_NAME="askcgsim-base"

PORT=$((18000 + SLURM_JOB_ID % 20000))

GPU_NODE=$(hostname -s)
INFO_FILE=$PSCRATCH/BaseLLM_vllm_${SLURM_JOB_ID}.env

cat > "$INFO_FILE" <<EOF
GPU_NODE=$GPU_NODE
PORT=$PORT
BASE_URL=http://$GPU_NODE:$PORT/v1
MODEL_NAME=$SERVED_MODEL_NAME
EOF

echo "vLLM service info written to:"
echo "$INFO_FILE"
cat "$INFO_FILE"

if [ -n "${SLURM_STEP_GPUS:-}" ]; then
    GPU_SLOT="$(echo "${SLURM_STEP_GPUS}" | cut -d',' -f1)"
    export CUDA_VISIBLE_DEVICES="${GPU_SLOT}"
else
    export CUDA_VISIBLE_DEVICES="$(echo "${CUDA_VISIBLE_DEVICES:-0}" | cut -d',' -f1)"
fi

srun shifter \
    --image=docker:vllm/vllm-openai:latest \
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

        vllm serve $MODEL_ID \
            --served-model-name $SERVED_MODEL_NAME \
            --host 0.0.0.0 \
            --port $PORT \
            --dtype auto \
            --gpu-memory-utilization 0.9 \
            --max-model-len 8192
    "