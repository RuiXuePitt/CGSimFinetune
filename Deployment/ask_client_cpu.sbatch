#!bin/bash
#SBATCH --job-name=Ask-Client-CPU
#SBATCH --account=m2616
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --qos=regular
#SBATCH --time=00:10:00
#SBATCH --output=logs/slurm-ask-client-cpu-%j.out

set -euo pipefail

cd $HOME/CGSimFinetune
mkdir -p logs

ENV_FILE="$1"
QUESTION="$2"

srun shifter \
    --image=docker:pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime \
    --volume "$PSCRATCH:/scratch" \
    --volume "$HOME/CGSimFinetune/Deployment:/workspace" \
    bash -lc "
        set -euo pipefail
        cd /workspace
        python -c 'import requests, argparse, json, time; print(\"Python client env OK\")'
        python client.py -i \"$ENV_FILE\" -u \"$QUESTION\"
    "