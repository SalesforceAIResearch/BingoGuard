export CUDA_VISIBLE_DEVICES=1,2,3,4
array=("safety_bingo_training_v6_iter2_filtered_v3_with_prompt_cls")
for i in ${array[@]}; do
    echo $i
    echo "microsoft/Phi-3-mini-4k-instruct"
    accelerate launch --main_process_port 25001 --config_file=examples/accelerate_configs/deepspeed_zero3.yaml --num_processes 4 examples/scripts/sft_completion.py \
        --dataset_name "fanyin3639/$i" \
        --model_name_or_path "microsoft/Phi-3-mini-4k-instruct" \
        --learning_rate=2e-6 \
        --warmup_ratio 0.1 \
        --bf16 \
	--save_strategy "epoch" \
	--save_total_limit 5 \
        --per_device_train_batch_size=1 \
        --gradient_accumulation_steps=32 \
        --output_dir="$i-phi3-2e-6" \
        --logging_steps=1 \
        --num_train_epochs=2 \
        --max_seq_length=4096 \
        --max_steps=-1 \
        --gradient_checkpointing
done

