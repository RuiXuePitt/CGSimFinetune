#!/bin/bash

# Quick Deploy Base Model + LoRA Adapter Through vLLM, using salloc
# Rui Xue

salloc -C "gpu&hbm40g" -q interactive -t 00:30:00 -A m2616_g --gpus 1 srun --pty bash -lc '
echo "================================================================================"
echo "RUN QUICK Base Model + LoRA Adapter Model vLLM Deploy"
echo "================================================================================"

cd $HOME/CGSimFinetune
mkdir -p $PSCRATCH/.hf

unset SSL_CERT_FILE REQUESTS_CA_BUNDLE CURL_CA_BUNDLE
export HF_HOME=$PSCRATCH/.hf
export HF_HUB_CACHE=$PSCRATCH/.hf/hub
export CUDA_VISIBLE_DEVICES="$(echo "${CUDA_VISIBLE_DEVICES:-0}" | cut -d, -f1)"
echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"

BASE_MODEL_ID="AI4SciNoob/Llama-3.1-Nemotron-Nano-8B-v1-AskCGSim"
SERVED_MODEL_NAME="askcgsim-base"
LORA_MODEL_NAME="askcgsim-ft"
LORA_ADAPTER="$PSCRATCH/run/nemotron-llama8b-CGsim_highqual_onlySQL/checkpoints/checkpoint-210"

PORT=$((18000 + SLURM_JOB_ID % 20000))

GPU_NODE=$(hostname -s)
INFO_FILE=$PSCRATCH/FineTunedLLM_V1_vllm.env

cat > "$INFO_FILE" <<EOF
GPU_NODE=$GPU_NODE
PORT=$PORT
BASE_URL=http://$GPU_NODE:$PORT/v1
MODEL_NAME=$LORA_MODEL_NAME
EOF

echo ""
echo "================================================================================"
echo "vLLM service info written to:"
echo "$INFO_FILE"
cat "$INFO_FILE"
echo "================================================================================"
echo ""

shifter \
    --image=docker:vllm/vllm-openai:latest \
    --module=gpu \
    --env HF_HOME=$HF_HOME \
    --env HF_HUB_CACHE=$HF_HUB_CACHE \
    --env CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES \
    bash -lc "
        set -euo pipefail

        vllm serve $BASE_MODEL_ID \
            --enable-lora \
            --lora-modules $LORA_MODEL_NAME=$LORA_ADAPTER \
            --served-model-name $SERVED_MODEL_NAME \
            --host 0.0.0.0 \
            --port $PORT \
            --dtype auto \
            --gpu-memory-utilization 0.9 \
            --max-model-len 8192
    "
'