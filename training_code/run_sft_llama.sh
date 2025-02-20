export CUDA_VISIBLE_DEVICES=0,1,2,7
export HF_HOME='/data2/fanyin/.cache'
array=("Meta-Llama-3.1-8B")
for i in ${array[@]}; do
    echo $i
    echo "meta-llama/Meta-Llama-3.1-8B-Instruct"
    echo "microsoft/Phi-3-mini-4k-instruct"
    accelerate launch --main_process_port 25001 --config_file=examples/accelerate_configs/deepspeed_zero3.yaml --num_processes 4 examples/scripts/sft_completion_llama.py \
        --dataset_name "fanyin3639/safety_bingo_training_final_decontaminated_v1" \
        --model_name_or_path "meta-llama/$i" \
        --learning_rate=2e-6 \
        --warmup_ratio 0.03 \
        --bf16 \
	--save_strategy "epoch" \
	--save_total_limit 5 \
        --per_device_train_batch_size=2 \
        --gradient_accumulation_steps=16 \
        --output_dir="$i-final-2e-6" \
        --logging_steps=1 \
        --num_train_epochs=2 \
        --max_seq_length=4096 \
        --max_steps=-1 \
        --gradient_checkpointing
done

