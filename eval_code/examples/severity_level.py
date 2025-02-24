import argparse
import copy
import json
import torch
import os.path
import gc
import datasets
import random
from pathlib import Path
from severity_rubrics import Prompt_template, Prompt_template_zero_shot, per_type_example, per_type_rubrics
from huggingface_hub import login
from collections import OrderedDict, Counter
login(token = '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')

import pandas as pd
from ray.util import remove_placement_group
from evaluator import Evaluator
from metrics import eval_auprc, eval_f1, eval_macro_f1, eval_per_level_and_type_acc
from constant import *

THIS_FILE = Path(__file__).resolve()

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
    map = {'privacy': 'privacy invasion' , 'violence': 'Violent crime', 'sex_crime': 'Sex-related crime', 'sex_content': 'Sexual content', 'weapon': 'Weapon', 'ip': 'Intellectual property infringement', 'hate': 'Hate and discriminate', 'self_harm': 'Self-harm', 'nonviolent': 'Non-violent crime', 'misinformation': 'misinformation', 'profanity': 'profanity'}
    ds = []
    labels = []
    if 'safety_bingo_testset' in input_name:
        df = datasets.load_dataset(input_name, split='train')
        labels = []
        template_data = {"messages": [{"role": "user", "content": ""}, {"role": "assistant", "content": ""}]}
        column_names = [name for name in df.column_names if not name in ['prompt', 'response']]
        for data in df:

            template_data['messages'][0]['content'] = Prompt_template_zero_shot.format(category=map[data['category']],
                                                           rubrics=per_type_rubrics[map[data['category']]],
                                                           query=data['prompt'],
                                                           response=data['response'])


            for name in column_names:
                template_data[name] = data[name]

            ds.append(copy.deepcopy(template_data))

            labels.append(int(data['level'][-1]))

    return ds, labels


if __name__ == "__main__":
    args = parse_args()
    # Read example data
    messages, labels = read_example_data(args.task_name)
    models = [args.model]

    for model in models:
        model_name = os.path.basename(os.path.normpath(model))
        print(f'Running {model} evaluation...')
        use_api = args.use_api or model == 'gpt-4o'
        template_policy = args.template_policy if not model == 'OpenSafetyLab/MD-Judge-v0.1' else 'domain'
        LLM_safe_guard = Evaluator(
            str(model), template_policy=template_policy, use_vllm=args.use_vllm, use_flash_attn=args.use_flash, use_api=use_api
        )
        eval_labels, eval_classes = LLM_safe_guard.eval_severity_labels(messages)
        eval_macro_f1(labels, eval_labels, print_=True)
        eval_per_level_and_type_acc(labels, eval_labels, eval_labels, messages, print_=True)




