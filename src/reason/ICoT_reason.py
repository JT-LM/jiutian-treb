from prompts.sys_prompt import get_sys_prompt
from llm.vllmcaller import VLLMCaller,VLLMCallerConfig
import time
from sample_format.sample import Sample
from tqdm import tqdm
from result_parsers.result_parser import ResultParser
from util.str_op import has_code, get_code_before_i, split_by_last_tag
import copy

class ICoT_Reasoner(object):
    """
    The implemention of ICoT reasoning mode, where an interactive sandbox is used and the final result is parsed from \\boxed{}.
    """
    def __init__(self, config):
        self.config = config
        self.batch_size = config.reason_batch_size
        self.llmcaller = config.llmcaller
        self.result_parser = ResultParser(config)

    def prompt(self, sample, first_flag):
        """Create a prompt for the LLM to reason about the input_prompt."""
        sys_prompt = get_sys_prompt(sample, self.config)
        if first_flag:
            data_info = sample.get_data_info()
            rows, columns = sample.df.shape
            columns_list_str = sample.df_columns()
            prompt = f"""Table Path: /mnt/tmp.csv\n\nThe table data has been loaded into the variable `df`. Display the basic information of the table using `df.info`:\n {data_info}\n\nThis dataset contains {rows} rows and {columns} columns. The column names in the dataset are: {columns_list_str}\n\n Question:{sample.input_prompt}"""
            return [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ]
        else:
            return sample.history

    def parse(self, sample, response, i):
        response = sample.generation + response
        string = response
        
        string_code_before_i = get_code_before_i(string, i)
        if string_code_before_i == '' or i == -1:
            sample.generation = response
            sample.add_info['scot_finish'] = True
        else:
            sample.generation = string_code_before_i
            self.result_parser.parse([sample], 'code_persist')
            sample.generation += f"\n```CodeExecuteResult\n{sample.code_run_result}\n```\n"
            sample.add_info['scot_finish'] = False
        
        sys_prompt = get_sys_prompt(sample, self.config)
        data_info = sample.get_data_info()
        rows, columns = sample.df.shape
        columns_list_str = sample.df_columns()
        prompt = f"""Table Path: /mnt/tmp.csv\n\nThe table data has been loaded into the dataframe variable `df`. Display the basic information of the table using `df.info`:\n {data_info}\n\nThis dataset contains {rows} rows and {columns} columns. The column names in the dataset are: {columns_list_str}\n\n Question:{sample.input_prompt}"""
        history = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": sample.generation}
        ]
        
        sample.history = history
        
        return sample
    
    def judge_finish(self, samples):
        batch_ok = []
        batch_unfinish = []
        for sample in samples:
            if 'scot_finish' not in sample.add_info:
                sample.add_info['scot_finish'] = False
            if sample.add_info['scot_finish']:
                batch_ok.append(sample)
            else:
                batch_unfinish.append(sample)
        return batch_ok, batch_unfinish
    
    def reason_one_step(self, batch_unfinish, i):
        if i == 0:
            batch_prompt = [self.prompt(sample, first_flag=True) for sample in batch_unfinish]
        else:
            batch_prompt = [self.prompt(sample, first_flag=False) for sample in batch_unfinish]
        try:
            responses = self.llmcaller.call_batch(batch_prompt)
            new_samples_batch = [self.parse(batch_unfinish[k], responses[k], i) for k in range(len(batch_unfinish))]
        except Exception as e:
            print(f"An call_batch error occurred: {e}")
            batch_ok, batch_unfinish = self.judge_finish(batch_unfinish)
            return batch_ok, batch_unfinish
        batch_ok, batch_unfinish = self.judge_finish(new_samples_batch)
        return batch_ok, batch_unfinish
    
    def reason(self, samples, config):
        print('----------reason begin')
        save_reason_path = config.save_reason_path
        batch_size = self.batch_size
        new_samples = []
        for sample in samples:
            if sample.generation is not None and sample.generation != '':
                new_samples.append(sample)
            else:
                break
        start = len(new_samples)
        total_rows = len(samples)
        
        assert (total_rows - start) > 0
        
        for i in tqdm(range(start, total_rows, batch_size)):
            s = time.time()
            batch = samples[i : i + batch_size]
            batch_finish = []
            batch_unfinish = batch
            for j in range(3):
                if len(batch_unfinish) == 0:
                    break
                batch_ok, batch_unfinish = self.reason_one_step(batch_unfinish, j)
                batch_finish.extend(batch_ok)
            if len(batch_unfinish) > 0:
                batch_ok, batch_unfinish = self.reason_one_step(batch_unfinish, -1)
                batch_finish.extend(batch_ok)
            new_samples.extend(batch_finish)
            e = time.time()
            print(f"processed {i}:{i+batch_size} / {total_rows}, used {e-s} seconds")
        self.result_parser.parse(new_samples, 'boxed')      
        return new_samples

    