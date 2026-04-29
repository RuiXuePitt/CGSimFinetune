#!/bin/bash
salloc -C cpu -q interactive -t 00:10:00 -A m2616 srun --pty bash -lc '
set -euo pipefail

cd $HOME/CGSimFinetune
mkdir -p logs

ENV_FILE="$1"
QUESTION="$2"

shifter \
    --image=docker:pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime \
    --volume "$PSCRATCH:/scratch" \
    --volume "$HOME/CGSimFinetune/Deployment:/workspace" \
    bash -lc "
        set -euo pipefail
        cd /workspace
        python -c '\''import requests, argparse, json, time; print(\"Python client env OK\")'\''
        python client.py -i \"$ENV_FILE\" -u \"$QUESTION\"
    "
' bash "$1" "$2"