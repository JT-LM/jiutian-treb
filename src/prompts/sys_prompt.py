import os
import pandas as pd
import numpy as np
import prompts.common_prompt as common_prompt

def get_Table_Summary_instruct_prompt(config):
    prompt = common_prompt.TABLE_SUMMARY_PROMPT
    return prompt

def get_Table_Query_instruct_prompt(config):
    if config.mode in ['TCoT_md', 'TCoT_html']:
        prompt = common_prompt.TEXT_SYSTEM_PROMPT
    elif config.mode == 'PoT':
        prompt = common_prompt.PYTHON_SYSTEM_PROMPT
    elif config.mode == 'ICoT':
        prompt = common_prompt.ICOT_PYTHON_SYSTEM_PROMPT
    else:
        prompt = common_prompt.COMMON_SYSTEM_PROMPT
    prompt += """\n- The row and column counting of the table starts at the 1st row and 1st column."""
    return prompt

def get_common_prompt(config):
    if config.mode in ['TCoT_md', 'TCoT_html']:
        prompt = common_prompt.TEXT_SYSTEM_PROMPT
    elif config.mode == 'PoT':
        prompt = common_prompt.PYTHON_SYSTEM_PROMPT
    elif config.mode == 'ICoT':
        prompt = common_prompt.ICOT_PYTHON_SYSTEM_PROMPT
    else:
        prompt = common_prompt.COMMON_SYSTEM_PROMPT
    return prompt

def get_sys_prompt(sample, config):
    task_name = sample.id.split('|')[0]
    if task_name == 'Table_Summary':
        return get_Table_Summary_instruct_prompt(config)
    elif task_name == 'Table_Query':
        return get_Table_Query_instruct_prompt(config)
    else:
        return get_common_prompt(config)