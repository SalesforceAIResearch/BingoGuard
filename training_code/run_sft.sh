export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
export HF_HOME='your path to huggingface home'
MODELS=("microsoft/Phi-3-mini-4k-instruct" "meta-llama/Meta-Llama-3.1-8B")
for model in ${MODELS[@]}; do
    echo $model
    accelerate launch --main_process_port 25001 --config_file=examples/accelerate_configs/deepspeed_zero3.yaml --num_processes 4 examples/scripts/sft_completion_moderator.py \
        --dataset_name "data path" \
        --model_name_or_path $model \
        --learning_rate=2e-6 \
        --warmup_ratio 0.1 \
        --bf16 \
	--save_strategy "epoch" \
	--save_total_limit 5 \
        --per_device_train_batch_size=1 \
        --gradient_accumulation_steps=32 \
        --output_dir="$model-2e-6" \
        --logging_steps=1 \
        --num_train_epochs=2 \
        --max_seq_length=4096 \
        --max_steps=-1 \
        --gradient_checkpointing
done

