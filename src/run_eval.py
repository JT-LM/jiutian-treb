import json
import os
import argparse

from reason.PoT_reason import PoT_Reasoner
from reason.TCoT_reason import TCoT_Reasoner
from reason.ICoT_reason import ICoT_Reasoner
from judge.judger import Judger
from sample_format.sample import Sample

from llm.vllmcaller import VLLMCaller,VLLMCallerConfig

import time
import util.file_op as op

import warnings
warnings.filterwarnings("ignore")

import logging

logging.getLogger().setLevel(logging.WARNING)


class RunConfig:
    """
    Configuration for evaluation.
    """
    def __init__(self,
                version=None,
                round=1,
                dataset_name=None,
                task_path=None,
                run_step='reason',
                mode='PoT',
                if_instruction=0,
                if_title=0,
                metrics=["BLEU", "ROUGE", "EM", "LLM_score"],
                save_reason_path=None,
                save_judge_path=None,
                reason_batch_size=512,
                judge_batch_size=512,
                reason_model_name =None,
                reason_model_path=None,
                reason_model_cards=None,
                reason_max_model_len=None,
                judge_model_name=None,
                judge_model_path=None,
                judge_model_cards=None,
                judge_max_model_len=None,
                llmcaller=None
                ):
        self.version = version
        """Evaluation version."""
        
        self.round = round
        """Evaluation round."""
        
        self.dataset_name=dataset_name
        """Dataset to evaluate."""
        
        self.task_path = task_path
        """Source path of the dataset."""
        
        self.run_step = run_step
        """The current run step: reason/judge"""
        
        self.mode = mode
        """The reasoning mode: TCoT/TCoT_md/TCoT_html/PoT/ICoT"""
        
        self.if_instruction = if_instruction
        """Whether to use instruction in the dataset."""
        
        self.if_title = if_title
        """Whether to use table title in the dataset."""
        
        self.metrics = metrics
        """Evaluation metrics"""
        
        self.save_reason_path = save_reason_path
        """Saving path of reasoning step"""
        
        self.save_judge_path = save_judge_path
        """Saving path of judging step"""
        
        self.reason_batch_size = reason_batch_size
        """Reasoning batch size"""
        
        self.judge_batch_size = judge_batch_size
        """Judging batch size"""
        
        self.reason_model_name = reason_model_name
        """The reasoning LLM model name."""
        
        self.reason_model_path = reason_model_path
        """The reasoning LLM model path."""
        
        self.reason_model_cards = reason_model_cards
        """The reasoning LLM model cuda visible devices."""
        
        self.reason_max_model_len = reason_max_model_len
        """The reasoning LLM model max model len for vLLM configuration."""
        
        self.judge_model_name = judge_model_name
        """The judging LLM model name."""
        
        self.judge_model_path = judge_model_path
        """The judging LLM model path."""
        
        self.judge_model_cards = judge_model_cards
        """The judging LLM model cuda visible devices."""
        
        self.judge_max_model_len = judge_max_model_len
        """The judging LLM model max model len for vLLM configuration."""
        
        self.llmcaller = llmcaller
        """"An instance of VLLMCaller class."""
        
        

def run(config):
    
    for key, value in vars(config).items():
        print(f"  {key}: {value}")
    
    judger = Judger(config)
    if config.mode == 'PoT':
        reasoner = PoT_Reasoner(config)
    elif 'TCoT' in config.mode:
        reasoner = TCoT_Reasoner(config)
    elif config.mode == 'ICoT':
        reasoner = ICoT_Reasoner(config)
    else:
        raise ValueError(f"No matching mode found for '{config.mode}'")
    
    if config.run_step == 'reason':
        print(f'load eval data from {config.task_path}')
        samples = Sample.load_samples(config.task_path, config)
        samples = reasoner.reason(samples, config)
        Sample.save_samples(samples, config.save_reason_path)
        print(f'model: {config.reason_model_name} dataset:{config.dataset_name} reason complete!')
        print(f'save reason result: {config.save_reason_path}')
    elif config.run_step == 'judge':
        print(f'load reasoned data from {config.save_reason_path}')
        samples = Sample.load_samples(config.save_reason_path, config) 
        samples = judger.judge(samples)
        Sample.save_samples(samples, config.save_judge_path)   
        print(f'{config.reason_model_name} dataset:{config.dataset_name} judge complete!')
        print(f'save judge result: {config.save_judge_path}')
    else:
        raise ValueError(f"No matching run_step found for '{config.run_step}'")
    
    print('program complete!')
        
    
def main(config_info, run_step):
    
    if run_step == 'reason':
        caller_config = VLLMCallerConfig(model_name=config_info['model_config']['reason_model_name'], use_cards=config_info['model_config']['reason_model_cards'], llmpath=config_info['model_config']['reason_model_path'], max_model_len=config_info['model_config']['reason_max_model_len'], temperature=config_info['model_config']['reason_temperature'])
        llmcaller = VLLMCaller(caller_config)
    elif run_step == 'judge' and config_info['model_config']['judge_model_path'] != "":
        caller_config = VLLMCallerConfig(model_name=config_info['model_config']['judge_model_name'], use_cards=config_info['model_config']['judge_model_cards'], llmpath=config_info['model_config']['judge_model_path'], max_model_len=config_info['model_config']['judge_max_model_len'], temperature=0.2)
        llmcaller = VLLMCaller(caller_config)
    else:
        raise ValueError(f"No matching run_step found for '{run_step}'")
    
    for dataset_name in config_info['dataset_config']:
        for mode in config_info['dataset_config'][dataset_name]['reason_mode']:
            
            save_reason_path = f"../eval_output/{config_info['version']}/{config_info['model_config']['reason_model_name']}/{mode}--{dataset_name}--round{config_info['round']}--reason.jsonl"
            save_judge_path = f"../eval_output/{config_info['version']}/{config_info['model_config']['reason_model_name']}/{mode}--{dataset_name}--round{config_info['round']}--judge.jsonl"
    
            os.makedirs(os.path.dirname(save_reason_path), exist_ok=True)
            os.makedirs(os.path.dirname(save_judge_path), exist_ok=True)
            
            run_config = RunConfig(
                version=config_info['version'],
                round=config_info['round'],
                dataset_name=dataset_name,
                task_path=config_info['dataset_config'][dataset_name]['path'],
                run_step=run_step,
                mode=mode,
                if_instruction=config_info['dataset_config'][dataset_name]['if_instruction'],
                if_title=config_info['dataset_config'][dataset_name]['if_title'],
                metrics=config_info['dataset_config'][dataset_name]['metrics'],
                save_reason_path=save_reason_path,
                save_judge_path=save_judge_path,
                reason_batch_size=512,
                judge_batch_size=512,
                reason_model_name=config_info['model_config']['reason_model_name'],
                reason_model_path=config_info['model_config']['reason_model_path'],
                reason_model_cards=config_info['model_config']['reason_model_cards'],
                reason_max_model_len=config_info['model_config']['reason_max_model_len'],
                judge_model_name=config_info['model_config']['judge_model_name'],
                judge_model_path=config_info['model_config']['judge_model_path'],
                judge_model_cards =config_info['model_config']['judge_model_cards'],
                judge_max_model_len=config_info['model_config']['judge_max_model_len'],
                llmcaller = llmcaller
            )
    
            run(run_config)

if __name__ == '__main__':
    start_time = time.time()

    parser = argparse.ArgumentParser(description="Run script for dataset processing")

    parser.add_argument("--config", type=str, default='default', help="eval config")
    parser.add_argument("--run_step", type=str, default=None, help="reason or judge")

    args = parser.parse_args()
    config_info = op.read_dict_from_json(args.config)
    run_step = args.run_step
    
    print(config_info)
    print(run_step)

    print("Evaluation Configs:")
    print(config_info)
    
    main(config_info, run_step)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print('all program complete!')
    print(f"run time: {elapsed_time:.2f} seconds")