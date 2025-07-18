#!/bin/bash
set -e

############################################################
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('conda' 'shell.bash' 'hook' 2> /dev/null)"
eval "$__conda_setup"
unset __conda_setup
# <<< conda initialize <<<
############################################################


env_root=/hpc-cache-pfs/home/qilongwu/peptide-lead-optimization/model/molepsa_v1/env
conda activate $env_root
export LD_LIBRARY_PATH=${env_root}/lib:$LD_LIBRARY_PATH

export http_proxy=http://sys-proxy-rd-relay.byted.org:3128 https_proxy=http://sys-proxy-rd-relay.byted.org:3128 no_proxy=code.byted.org HTTP_PROXY=http://sys-proxy-rd-relay.byted.org:3128 HTTPS_PROXY=http://sys-proxy-rd-relay.byted.org:3128
export LAYERNORM_TYPE=fast_layernorm
export USE_DEEPSPEED_EVO_ATTENTION=true
export CUTLASS_PATH="/hpc-cache-pfs/home/xyj/code/cutlass"

N_sample=5
N_step=200
N_cycle=10
seed=101

input_json_path=$1
dump_dir=$2
seeds=$3
# export MMSEQS_SERVICE_HOST_URL=https://ai4s.bytedance.net/api/msa
export TORCH_EXTENSIONS_DIR=/hpc-cache-pfs/home/xyj/OUTPUT/torch_cache/torch_extensions

cd /hpc-cache-pfs/home/xyj/code/Protenix/
export PYTHONPATH="."
python3 -m runner.batch_inference \
--seeds ${seeds} \
--out_dir ${dump_dir} \
--input ${input_json_path} \
--use_msa_server

# The following is a demo to use DDP for inference
# torchrun \
#     --nproc_per_node $NPROC \
#     --master_addr $WORKER_0_HOST \
#     --master_port $WORKER_0_PORT \
#     --node_rank=$ID \
#     --nnodes=$WORKER_NUM \
#     runner/inference.py \
#     --seeds ${seed} \
#     --dump_dir ${dump_dir} \
#     --input_json_path ${input_json_path} \
#     --model.N_cycle ${N_cycle} \
#     --sample_diffusion.N_sample ${N_sample} \
#     --sample_diffusion.N_step ${N_step}