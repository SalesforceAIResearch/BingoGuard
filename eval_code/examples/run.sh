export CUDA_VISIBLE_DEVICES=6
export PYTHONPATH='../utils'
export HF_HOME='Your path to huggingface home'
export VLLM_WORKER_MULTIPROC_METHOD=spawn

LEVEL=("toxicchat" "oai" "aegis" 'xstest' 'harmbprompt' 'simplesafetytest' 'wildprompt')
MODEL=("/mnt/disks/sdb/fayin/bingoguard_initial/trl/Meta-Llama-3.1-8B-final-2e-6-w-severity-2-nodeco")
for i in "${LEVEL[@]}"
do
	echo $i
        # python binary.py --model allenai/wildguard --template_policy User --task $i --use-vllm
	python binary.py --model "your path to model" --template_policy User --task $i --use-vllm
done

LEVEL=("beavortails" "saferlhf" "xrtest" 'harmbench' 'wildguard' 'safety_bingo_testset' )
MODEL=("/export/home/trl/safety_bingo_training_v6_iter2_filtered_v4_more_beavortails_with_prompt_cls-phi3-2e-6")
for i in "${LEVEL[@]}"
do
        echo $i
        # python binary.py --model allenai/wildguard --template_policy User --task $i --use-vllm
        python binary.py --model "your path to model" --template_policy Agent --task $i --use-vllm
done

