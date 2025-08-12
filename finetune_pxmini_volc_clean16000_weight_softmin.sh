# Copyright 2024 ByteDance and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

export LAYERNORM_TYPE=fast_layernorm
export USE_DEEPSPEED_EVO_ATTENTION=true

export PYTHONPATH="."
export PROTENIX_DATA_ROOT_DIR="/voyager-hackathon/dataland/af3-dev/release_data"
export CUTLASS_PATH="/opt/cutlass"

## the proxy setting below is typycally used for wandb
export http_proxy=http://100.68.163.252:3128 https_proxy=http://100.68.163.252:3128 HTTP_PROXY=http://100.68.163.252:3128 HTTPS_PROXY=http://100.68.163.252:3128

# export TORCH_EXTENSIONS_DIR="/hpc-cache-pfs/home/.cache/torch_cache/torch_extensions_a100"
# export TORCH_CUDA_ARCH_LIST="7.0;8.0;9.0"
# wget -P /af3-dev/release_model/ https://af3-dev.tos-cn-beijing.volces.com/release_model/protenix_base_default_v0.5.0.pt
checkpoint_path="/voyager-hackathon/dataland/af3-dev/protenix_ckpts/protenix_mini_default_v0.5.0.pt"

export TORCH_EXTENSIONS_DIR=/voyager-hackathon/home/.cache/torch_extensions

wandb login --relogin f7236ac4c913eee1f79561215edc9b95a992c351 ## your wandb token

torchrun \
--nproc_per_node $MLP_WORKER_GPU \
--master_addr $MLP_WORKER_0_HOST \
--node_rank $MLP_ROLE_INDEX \
--master_port $MLP_WORKER_0_PORT \
--nnodes $MLP_WORKER_NUM \
/voyager-hackathon/home/hms/code/Protenix/runner/train.py \
--model_name "protenix_mini_default_v0.5.0" \
--run_name volc_clean_16000_weight_softmin \
--seed 42 \
--base_dir ./output \
--dtype bf16 \
--project protenix_finetune_md_volc \
--use_wandb true \
--diffusion_batch_size 48 \
--eval_interval 100 \
--log_interval 5 \
--checkpoint_interval 100 \
--ema_decay 0.999 \
--train_crop_size 384 \
--max_steps 2500 \
--lr 0.0018 \
--load_checkpoint_path ${checkpoint_path} \
--load_ema_checkpoint_path ${checkpoint_path} \
--data.train_sets md0805_trainingset \
--data.test_sets md0805_testset1 \
--data.md0805_testset1.base_info.max_n_token 500 \
--data.md0805_trainingset.base_info.indices_fpath /voyager-hackathon/home/hms/code/Protenix/mydata/md0805_training_ligand_prot_clean_weights.csv \
--data.epoch_size 16000 \
--loss.diffusion_mse_loss_softmin true \
--data.md0805_trainingset.sampler_configs.force_recompute_weight false