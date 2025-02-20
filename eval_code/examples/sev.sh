export CUDA_VISIBLE_DEVICES=0
export VLLM_WORKER_MULTIPROC_METHOD=spawn
LEVEL=("fanyin3639/safety_bingo_testset")
MODEL=("OpenSafetyLab/MD-Judge-v0.1" "meta-llama/Meta-Llama-Guard-2-8B" "meta-llama/Llama-Guard-3-8B" "allenai/wildguard" "/export/home/trl/safety_bingo_training_v6_iter2_filtered_v4_more_beavortails_with_prompt_cls-phi3-2e-6")
python severity_level.py --use_api --per_level --mode auprc --model gpt-4o  --template_policy Severity --task "fanyin3639/safety_bingo_testset" --use-vllm
assert(0)
for i in "${LEVEL[@]}"
do
	echo $i
	python example.py --per_level --mode auprc --model OpenSafetyLab/MD-Judge-v0.1 --template_policy Agent --task $i --use-vllm
	python example.py --per_level --model allenai/wildguard --template_policy Agent --task $i --use-vllm
	python example.py --per_level --model /export/home/trl/safety_bingo_training_v6_iter2_filtered_v4_more_beavortails_with_prompt_cls-phi3-2e-6 --template_policy Agent --task $i --use-vllm
done
