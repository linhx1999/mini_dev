#!/usr/bin/env bash

eval_path='/root/autodl-tmp/workspace/kouan/datasets/bird/dev/dev.json'
db_root_path='/root/autodl-tmp/workspace/kouan/datasets/bird/dev/dev_databases/'
use_knowledge='False'
mode='dev'  # dev, train, mini_dev
cot='False'
sql_dialect='SQLite'
data_output_path='./exp_result/turbo_output/'

api_base=http://127.0.0.1:8000/v1
api_key=EMPTY
engine='Qwen2.5-Coder-7B-Instruct'

num_threads=4
max_tokens=16384

echo "generate $engine batch for $mode, run in $num_threads threads, with knowledge: $use_knowledge, with chain of thought: $cot"
python3 -u llm/src/gpt_request.py \
  --db_root_path "${db_root_path}" \
  --api_key "${api_key}" \
  --api_base "${api_base}" \
  --mode "${mode}" \
  --engine "${engine}" \
  --eval_path "${eval_path}" \
  --data_output_path "${data_output_path}" \
  --use_knowledge "${use_knowledge}" \
  --chain_of_thought "${cot}" \
  --num_processes "${num_threads}" \
  --max_tokens "${max_tokens}" \
  --sql_dialect "${sql_dialect}"
