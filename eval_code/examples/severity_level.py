import argparse
import copy
import json
import torch
import os.path
import gc
import datasets
import random
from pathlib import Path
from saladbench.severity_rubrics import Prompt_template, per_type_example, per_type_rubrics
from huggingface_hub import login
from collections import OrderedDict, Counter
login(token = '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')

import pandas as pd
from ray.util import remove_placement_group
from saladbench.evaluator import DDPMDJudgeEvaluator, Evaluator
from saladbench.metrics import eval_auprc, eval_f1, eval_macro_f1, eval_calibration, eval_per_level_and_type_acc

BEAVORTAIL = 'PKU-Alignment/BeaverTails'
XSTEST = '/export/home/safety-bingo/exaggerated-safety/model_completions/xstest_v2_completions_mistralinstruct.csv'
TOXICCHAT = "lmsys/toxic-chat"
OAI = "/export/home/safety-bingo/moderation-api-release/data/samples-1680.jsonl"
AEGIS = 'nvidia/Aegis-AI-Content-Safety-Dataset-1.0'
HARMBENCH = '/export/home/safety-bingo/harmbench_text_behaviors_val_set.json'
WILDGUARD = 'allenai/wildguardmix'

THIS_FILE = Path(__file__).resolve()
# User should symlink checkpoint folder to `checkpoint` under parent directory.
EXAMPLE_QA = THIS_FILE.parent / "example_qa.jsonl"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task_name", type=str, default='xstest', help="Example QAs to evaluate"
    )
    parser.add_argument(
        "--model",
        type=str,
        default='OpenSafetyLab/MD-Judge-v0.1',
        help="Path to the model checkpoint. See README.md for preparing the checkpoint.",
    )
    parser.add_argument(
        "--mode",
        choices=["auprc", "safe", "both"],
        type=str,
        default="safe",
        help="Evaluate AUPRC or safety judgement or both.",
    )
    parser.add_argument(
        "--per_level",
        action="store_true",
        help="Calculate per level acc",
    )
    parser.add_argument(
        "--template_policy",
        choices=["Agent", "User", "Severity"],
        type=str,
        default="User",
        help="Evaluate AUPRC or safety judgement or both.",
    )
    parser.add_argument(
        "--use-vllm",
        action="store_true",
        help="Use vLLM for high throughput evaluation, only applicable for text generation.",
    )
    parser.add_argument(
        "--use_api",
        action="store_true",
        help="Use vLLM for high throughput evaluation, only applicable for text generation.",
    )
    parser.add_argument(
        "--use-flash",
        action="store_true",
        help="Use flash attention for high throughput evaluation.",
    )
    parser.add_argument(
        "--ddp",
        action="store_true",
        help="Enable data parallel on multiple GPUs.",
    )

    return parser.parse_args()


def read_example_data(input_name='beavortail', requries_reformat=False):
    template_data = {"messages": [{"role": "user", "content": ""}, {"role": "assistant", "content": ""}]}
    print(list(per_type_rubrics.keys()))
    map = {'privacy': 'privacy invasion' , 'violence': 'Violent crime', 'sex_crime': 'Sex-related crime', 'sex_content': 'Sexual content', 'weapon': 'Weapon', 'ip': 'Intellectual property infringement', 'hate': 'Hate and discriminate', 'self_harm': 'Self-harm', 'nonviolent': 'Non-violent crime', 'misinformation': 'misinformation', 'profanity': 'profanity'}
    ds = []
    labels = []
    print(input_name)
    if 'safety_bingo_testset' in input_name:
        df = datasets.load_dataset(input_name, split='train')
        print(Counter(df['level']))
        labels = []
        template_data = {"messages": [{"role": "user", "content": ""}, {"role": "assistant", "content": ""}]}
        column_names = [name for name in df.column_names if not name in ['prompt', 'response']]
        print(column_names)
        for data in df:

            # template_data['messages'][0]['content'] = data['prompt']
            # template_data['messages'][1]['content'] = data['target_response']
            # template_data['severity'] = data['response_severity']
            # ds.append(copy.deepcopy(template_data))
            # labels.append(0 if "vel: 0" in data['response_severity'] else 1)
            template_data['messages'][0]['content'] = Prompt_template.format(category=map[data['category']],
                                                           rubrics=per_type_rubrics[map[data['category']]],
                                                           query=data['prompt'],
                                                           examples=per_type_example[map[data['category']]],
                                                           response=data['response'])

            for name in column_names:
                template_data[name] = data[name]

            # template_data['severity'] = data['rewrite_severity']
            ds.append(copy.deepcopy(template_data))

            labels.append(int(data['level'][-1]))

    return ds, labels


if __name__ == "__main__":
    args = parse_args()
    # Read example data
    messages, labels = read_example_data(args.task_name)
    # Initialize Evaluator

    models = [args.model]
    # models = ['/export/home/trl/safety_bingo_training_v5_with_prompt_cls-llama3.1-2e-6']

    # new_data = {'prompt': [], 'response': [], 'original_label': []}
    # # column_names = [key for key in messages[0].keys() if not key == 'messages']
    # # print(column_names)
    # # for name in column_names:
    # #     new_data[name] = []
    # for data, label in zip(messages, labels):
    #
    #     new_data['prompt'].append(data['messages'][0]['content'])
    #     new_data['response'].append(data['messages'][1]['content'])
    #     new_data['original_label'].append(label)
    # if args.task_name == 'safebingo_response':
    #     new_data = datasets.load_from_disk('Llama-Guard-3-8B_safebingo_response')
    # else:
    #     new_data = datasets.load_from_disk('Llama-Guard-3-8B_safebingo_prompt')
    for model in models:
        model_name = os.path.basename(os.path.normpath(model))
        print(f'Running {model} evaluation...')
        use_api = args.use_api or model == 'gpt-4o'
        template_policy = args.template_policy if not model == 'OpenSafetyLab/MD-Judge-v0.1' else 'domain'
        LLM_safe_guard = Evaluator(
            str(model), template_policy=template_policy, use_vllm=args.use_vllm, use_flash_attn=args.use_flash, use_api=use_api
        )
        eval_labels, eval_clses = LLM_safe_guard.eval_severity_labels(messages)
        eval_macro_f1(labels, eval_labels, print_=True)




