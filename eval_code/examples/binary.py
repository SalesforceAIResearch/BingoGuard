## Code modified from SALAD_BENCH
## Original License: Apache License 2.0
## https://github.com/OpenSafetyLab/SALAD-BENCH

import argparse
import copy
import json
import torch
import os.path
import gc
import datasets
import random
from pathlib import Path
from huggingface_hub import login
from collections import OrderedDict, Counter
from constant import *

import pandas as pd
from ray.util import remove_placement_group
from evaluator import DDPMDJudgeEvaluator, Evaluator
from metrics import eval_auprc, eval_f1, eval_per_level_and_type_acc
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
        choices=["Agent", "User"],
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
        "--use-api",
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
    ds = []
    labels = []
    print(input_name)
    if 'beavortails' in input_name:
        df = datasets.load_dataset(BEAVORTAIL, split='30k_test')
        for data in df:
            template_data['messages'][0]['content'] = data['prompt']
            template_data['messages'][1]['content'] = data['response']
            ds.append(copy.deepcopy(template_data))
        labels = [1 - int(label) for label in df["is_safe"]]
    if 'simplesafetytest' in input_name:
        df = datasets.load_dataset('Bertievidgen/SimpleSafetyTests', split='test')
        for data in df:
            template_data['messages'][0]['content'] = data['prompt']
            ds.append(copy.deepcopy(template_data))
        labels = [1 for label in df["prompt"]]
    elif 'xstest' in input_name:
        df = pd.read_csv(XSTEST)
        df = datasets.Dataset.from_pandas(df)
        for data in df:
            template_data['messages'][0]['content'] = data['prompt']
            template_data['messages'][1]['content'] = data['completion']
            ds.append(copy.deepcopy(template_data))
        labels = [1 if 'contrast' in data['type'] else 0 for data in df]
    elif 'toxicchat' in input_name:
        df = datasets.load_dataset(TOXICCHAT, name='toxicchat0124', split='test')
        for data in df:
            template_data['messages'][0]['content'] = data['user_input']
            template_data['messages'][1]['content'] = data['model_output']
            ds.append(copy.deepcopy(template_data))
        labels = [int(data['toxicity']) == 1 for data in df]
    elif 'aegis' in input_name:
        df = datasets.load_dataset(AEGIS, split='test')
        df = df.filter(lambda example: example['text_type'] == 'user_message')
        for data in df:
            template_data['messages'][0]['content'] = data['text']
            ds.append(copy.deepcopy(template_data))
        labels = []
        for data in df:
            if not data['labels_0'] == 'Safe' and not data['labels_1'] == 'Safe' and not data['labels_2'] == 'Safe':
                labels.append(1)
            else:
                labels.append(0)
    elif 'oai' in input_name:
        with open(OAI, 'r') as f:
            df = f.readlines()

        for data in df:
            data = json.loads(data)
            template_data['messages'][0]['content'] = data['prompt']
            ds.append(copy.deepcopy(template_data))
        labels = []
        # ["S", "H", "V", "HR", "SH", "S3", "H2", "V2"]
        for data in df:
            data = json.loads(data)
            label = 0
            for value in data.values():
                if value == 1:
                    label = 1
                    break
            labels.append(copy.deepcopy(label))
    elif 'harmbprompt' in input_name:
        df = pd.read_csv('/data2/fanyin/SALAD-BENCH/harmbench_behaviors_text_test.csv', sep=',')
        # Filter to only "standard" or "copyright" FunctionalCategory
        # (remove "contextual" and "multimodal")
        df = df[df["FunctionalCategory"].isin(["standard", "copyright"])]

        ds = []
        for i, row in df.iterrows():
            template_data['messages'][0]['content'] = row["Behavior"]
            ds.append(copy.deepcopy(template_data))

        labels = [1 for _ in ds]

    elif 'saferlhf' in input_name:
        dataset = datasets.load_dataset("PKU-Alignment/PKU-SafeRLHF", revision="v0")
        test_dataset = dataset["test"]
        all_data = []
        ds = []

        prompts = test_dataset["prompt"]
        response_0 = test_dataset["response_0"]
        response_1 = test_dataset["response_1"]
        is_response_0_safe = test_dataset["is_response_0_safe"]
        is_response_1_safe = test_dataset["is_response_1_safe"]

        safe_responses, harmful_responses = [], []
        for p, r0, r1, r0s, r1s in zip(prompts, response_0, response_1, is_response_0_safe, is_response_1_safe):
            # pick only when r0s != r1s
            if r0s == r1s:
                continue
            if r0s:
                safe_responses.append({
                    "prompt": p,
                    "response": r0,
                    "response_harmfulness": 0,
                })
            else:
                harmful_responses.append({
                    "prompt": p,
                    "response": r0,
                    "response_harmfulness": 1,
                })

            if r1s:
                safe_responses.append({
                    "prompt": p,
                    "response": r1,
                    "response_harmfulness": 0,
                })
            else:
                harmful_responses.append({
                    "prompt": p,
                    "response": r1,
                    "response_harmfulness": 1,
                })

        # pick 1000 from each category
        random.seed(42)
        indices = random.sample(range(len(safe_responses)), 1000)
        all_data = [safe_responses[i] for i in indices] + [harmful_responses[i] for i in indices]

        for data in all_data:
            template_data['messages'][0]['content'] = data['prompt']
            template_data['messages'][1]['content'] = data['response']
            ds.append(copy.deepcopy(template_data))
        labels = [0 for i in range(1000)] + [1 for i in range(1000)]

    elif 'harmbench' in input_name:

        with open(HARMBENCH, 'r') as f:
            raw_data = json.load(f)
        keys = list(raw_data.keys())
        all_data = []
        ds = []
        def preprocess_data(x):
            # x includes human_0, human_1, human_2.
            # if more than two have 1, then it is harmful.
            # if more than two have 0, then it is non-harmful.
            human_0 = x["human_0"]
            human_1 = x["human_1"]
            human_2 = x["human_2"]

            harmfulness = 1 if sum(
                [human_0, human_1, human_2]) > 1 else 0
            is_adversarial = True if x["experiment"] != "default" else False
            return {"prompt": x["test_case"], "response": x["generation"], "response_harmfulness": harmfulness,
                    "prompt_type": "adversarial" if is_adversarial else "vanilla"}

        for k in keys:
            all_data.extend([preprocess_data(x) for x in raw_data[k]])
        for data in all_data:
            template_data['messages'][0]['content'] = data['prompt']
            template_data['messages'][1]['content'] = data['response']
            ds.append(copy.deepcopy(template_data))
        labels = [data["response_harmfulness"] == 1 for data in all_data]
    elif 'xrtest' in input_name:
        df = datasets.load_dataset("allenai/xstest-response", split="response_harmfulness")
        for data in df:
            template_data['messages'][0]['content'] = data['prompt']
            template_data['messages'][1]['content'] = data['response']
            ds.append(copy.deepcopy(template_data))
        labels = [label == 'harmful' for label in df["label"]]
    elif 'wildguard' in input_name:
        df = datasets.load_dataset(WILDGUARD, name='wildguardtest', split='test')
        for data in df:
            template_data['messages'][0]['content'] = data['prompt']
            template_data['messages'][1]['content'] = data['response']
            ds.append(copy.deepcopy(template_data))
        labels = [label == 'harmful' for label in df["response_harm_label"]]
    elif 'wildprompt' in input_name:
        df = datasets.load_dataset(WILDGUARD, name='wildguardtest', split='test')
        for data in df:
            template_data['messages'][0]['content'] = data['prompt']
            template_data['messages'][1]['content'] = data['response']
            ds.append(copy.deepcopy(template_data))
        labels = [label == 'harmful' for label in df["prompt_harm_label"]]
    elif 'safety_bingo_testset' in input_name:
        df = datasets.load_dataset(input_name, split='train')
        labels = []
        template_data = {"messages": [{"role": "user", "content": ""}, {"role": "assistant", "content": ""}]}
        column_names = [name for name in df.column_names if not name in ['prompt', 'response']]
        for data in df:
            template_data['messages'][0]['content'] = data['prompt']
            template_data['messages'][1]['content'] = data['response']
            for name in column_names:
                template_data[name] = data[name]

            # template_data['severity'] = data['rewrite_severity']
            ds.append(copy.deepcopy(template_data))

            labels.append(1)

    return ds, labels


if __name__ == "__main__":
    args = parse_args()
    # Read example data
    messages, labels = read_example_data(args.task_name)
    # Initialize Evaluator

    models = [args.model]
    
    for model in models:
        model_name = os.path.basename(os.path.normpath(model))
        print(f'Running {model} evaluation...')
        use_api = model == 'gpt-4o'
        template_policy = args.template_policy if not model == 'OpenSafetyLab/MD-Judge-v0.1' else 'domain'
        LLM_safe_guard = Evaluator(
            str(model), template_policy=template_policy, use_vllm=args.use_vllm, use_flash_attn=args.use_flash, use_api=use_api
        )
        if args.mode.lower() == "both" or args.mode.lower() == "auprc":
            eval_probs = LLM_safe_guard.eval_unsafe_probs(messages, batch_size=8)
            eval_labels, eval_clses = LLM_safe_guard.eval_unsafe_labels(messages)
            print("=" * 20 + "Evaluate AUPRC" + "=" * 20)
            auprc = eval_auprc(labels, eval_probs, print_=True)
            if args.per_level:
                df = datasets.load_dataset(args.task_name, split='train')
                df = df.add_column('probs', eval_probs)
                lens = [len(x) for x in df['prompt']]
                df = df.add_column('lens', lens)
                df = df.sort("lens")
                eval_per_level_and_type_acc(labels, eval_labels, eval_probs, messages, print_=True)
        if args.mode.lower() == "both" or args.mode.lower() == "safe":
            eval_labels, eval_clses = LLM_safe_guard.eval_unsafe_labels(messages)
            (accuracy, precision, fpr, recall, f1) = eval_f1(labels, eval_labels, print_=True)
            if args.per_level:
                eval_per_level_and_type_acc(labels, eval_labels, eval_labels, messages, print_=True)

        with open('wrong_examples.json', 'a') as f:
            for idx, (g, p) in enumerate(zip(labels, eval_labels)):
                if not g == p and int(g) == 0:
                    messages[idx]['policy_type'] = args.template_policy
                    messages[idx]['task_name'] = args.task_name
                    f.write(json.dumps(messages[idx]))
                    f.write('\n')

