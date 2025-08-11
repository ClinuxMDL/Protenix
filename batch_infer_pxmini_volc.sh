#!/bin/bash


load_checkpoint_fn=$1
test_mode=$2

if [ -z ${load_checkpoint_fn} ]; then
    echo "load_checkpoint_fn is empty"
    exit 1
fi

load_checkpoint_dir=$(dirname ${load_checkpoint_fn})
checkpoint_name=$(basename ${load_checkpoint_fn})


dump_dir="${load_checkpoint_dir}/results_${checkpoint_name}"

N_sample=20
seed="101,102,103,104,105"
N_step=5
N_cycle=4


model_name="protenix_mini_default_v0.5.0"
input_json_path=/voyager-hackathon/dataland/af3-dev/release_data/${test_mode}_Input_Json_Split_N_8/merged_split_${MLP_ROLE_INDEX}.json

export LAYERNORM_TYPE=fast_layernorm
export USE_DEEPSPEED_EVO_ATTENTION=true
export TORCH_EXTENSIONS_DIR=/voyager-hackathon/home/.cache/torch_extensions
export CUTLASS_PATH=/opt/cutlass
export PYTHONPATH="."

python3  runner/inference.py \
    --load_checkpoint_dir ${load_checkpoint_dir} \
    --model_name ${model_name} \
    --seeds ${seed} \
    --dump_dir ${dump_dir} \
    --input_json_path ${input_json_path} \
    --sample_diffusion.N_sample ${N_sample} \
    --sample_diffusion.N_step ${N_step} \
    --model.N_cycle ${N_cycle} 