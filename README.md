# README

A repo containing all the basic file templates and general guidelines for any AI open source project at Salesforce.

## Ethical Considerations
This release is for research purposes only in support of an academic paper. Our models, datasets, and code are not specifically designed or evaluated for all downstream purposes. We strongly recommend users evaluate and address potential concerns related to accuracy, safety, and fairness before deploying this model. We encourage users to consider the common limitations of AI, comply with applicable laws, and leverage best practices when selecting use cases, particularly for high-risk scenarios where errors or misuse could significantly impact people’s lives, rights, or safety. For further guidance on use cases, refer to our AUP and AI AUP.

## Usage

It's required that all files must be placed at the top level of your repository.

> **NOTE** Your README should contain detailed, useful information about the project!
=======
Code for **BingoGuard: LLM Content Moderation Tools with Risk Levels**.

Accepted as poster paper at ICLR 2025.

## Overview
In this paper, we introduce per-topic severity rubrics for 11 harmful topics and build BingoGuard, an LLM-based moderation system designed to predict both binary safety labels and severity levels. We create BingoGuardTrain, a training dataset with 54,897 examples covering a variety of topics, response severity, styles, and BingoGuardTest, a test set with 988 examples explicitly labeled based on our severity rubrics that enables fine-grained analysis on model behaviors on different severity levels.

Our BingoGuard-llama3.1-8B, trained on BingoGuardTrain, achieves the state-of-the-art performance on several moderation benchmarks, including WildGuardTest and HarmBench, as well as our in-domain test set BingoGuardTest, outperforming best public models, WildGuard, by 4.3\%.

This repository contains the training and evaluation code for BingoGuard.

## Environment
For inference, please install the environment based on the provided requirements.txt file. We use [vllm](https://github.com/vllm-project/vllm) for accelerated inference process.
```shell
pip install -r requirements.txt
```

For training, please download and install [huggingface-trl](https://github.com/huggingface/trl)
```shell
git clone https://github.com/huggingface/trl.git
cd trl
python setup.py develop
```
Then, move the files inside [training_code](https://github.com/fanyin3639/bingoguard_initial/tree/main/training_code) into trl/examples/scripts

## Run the code
For inference, we tested on the following datasets:
Prompt classification
* [Toxicchat](https://huggingface.co/datasets/lmsys/toxic-chat)
* [OpenAI-Moderation-API](https://github.com/openai/moderation-api-release)
* [Aegis](https://huggingface.co/datasets/nvidia/Aegis-AI-Content-Safety-Dataset-1.0)
* [XSTest](https://github.com/paul-rottger/xstest)
* [WildGuardTest](https://huggingface.co/datasets/allenai/wildguardmix)

Response classification
* [WildGuardTest](https://huggingface.co/datasets/allenai/wildguardmix)
* [Beavertails](https://huggingface.co/datasets/PKU-Alignment/BeaverTails)
* [SafeRLHF](https://huggingface.co/datasets/PKU-Alignment/PKU-SafeRLHF)
* [HarmBench](https://www.harmbench.org/)

We have included a script to evaluate on all the above datasets. Download the above datasets if necessary and write your file path in to eval_code/examples/constant. Then, simply run:
```shell
cd eval_code/examples
bash run.sh
```

If you would also like to evaluate on the severity level classification task, run
```shell
bash sev.sh
```

For training, please navigate into

```shell
cd trl/trl/examples/scripts/
```

Then, run
```shell
bash run_sft.sh
```

Change the base model in run_sft.sh to the base model you want to start with. However, you might need to change the special tokens in sft_completion_moderator.py

## Citation
```bibtex
@inproceedings{
yin2025bingoguard,
title={BingoGuard: {LLM} Content Moderation Tools with Risk Levels},
author={Fan Yin and Philippe Laban and XIANGYU PENG and Yilun Zhou and Yixin Mao and Vaibhav Vats and Linnea Ross and Divyansh Agarwal and Caiming Xiong and Chien-Sheng Wu},
booktitle={The Thirteenth International Conference on Learning Representations},
year={2025},
url={https://openreview.net/forum?id=HPSAkIHRbb}
}
```