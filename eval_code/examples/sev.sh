export CUDA_VISIBLE_DEVICES=0
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export PYTHONPATH='../utils'
LEVEL=("fanyin3639/safety_bingo_testset")
MODEL=("OpenSafetyLab/MD-Judge-v0.1" "meta-llama/Meta-Llama-Guard-2-8B" "meta-llama/Llama-Guard-3-8B" "allenai/wildguard" "/export/home/trl/safety_bingo_training_v6_iter2_filtered_v4_more_beavortails_with_prompt_cls-phi3-2e-6")
python severity_level.py --per_level --mode auprc --model /mnt/disks/sdb/fayin/bingoguard_initial/trl/Meta-Llama-3.1-8B-final-2e-6-w-severity-2  --template_policy Severity --task "fanyin3639/safety_bingo_testset" --use-vllm
