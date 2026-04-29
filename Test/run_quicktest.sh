#!/bin/bash
salloc -C "gpu&hbm40g" -q interactive -t 00:10:00 -A m2616_g --gpus 1 srun --pty bash -lc '

    echo "================================================================================"
    echo "RUN QUICK TEST"
    echo "================================================================================"

    cd "$HOME/CGSimFinetune"
    mkdir -p "$PSCRATCH/.hf"

    unset SSL_CERT_FILE REQUESTS_CA_BUNDLE CURL_CA_BUNDLE

    export HF_HOME="$PSCRATCH/.hf"
    export HF_HUB_CACHE="$HF_HOME/hub"
    export TRANSFORMERS_CACHE="$HF_HOME/transformers"
    export HF_DATASETS_CACHE="$HF_HOME/datasets"
    export PATH="$HOME/.local/bin:$PATH"
    export CUDA_VISIBLE_DEVICES="$(echo "${CUDA_VISIBLE_DEVICES:-0}" | cut -d, -f1)"
    echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"

    shifter \
        --image=docker:pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime \
        --module=gpu \
        --env HF_HOME="$HF_HOME" \
        --env HF_HUB_CACHE="$HF_HUB_CACHE" \
        --env TRANSFORMERS_CACHE="$TRANSFORMERS_CACHE" \
        --env HF_DATASETS_CACHE="$HF_DATASETS_CACHE" \
        --env CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES" \
        --volume "$PSCRATCH:/scratch" \
        --volume "$PWD:/workspace" \
        bash -lc "
            cd /workspace
            unset SSL_CERT_FILE REQUESTS_CA_BUNDLE CURL_CA_BUNDLE
            echo \"Installing required packages...\"
            pip install --no-cache-dir -r requirements.txt
            echo \"================================================================================\"
            echo \"Start Testing\"
            echo \"================================================================================\"
            python Test/quicktest.py
        "
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "Test succeeded!"
    else
        echo "Test failed!"
    fi

    exit $EXIT_CODE
'