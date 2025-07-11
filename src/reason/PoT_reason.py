from prompts.sys_prompt import get_sys_prompt
from llm.vllmcaller import VLLMCaller,VLLMCallerConfig
import time
from sample_format.sample import Sample
from tqdm import tqdm
from result_parsers.result_parser import ResultParser

class PoT_Reasoner(object):
    """
    The implemention of PoT reasoning mode, where a sandbox is used to parse the final result.
    """
    def __init__(self, config):
        self.config = config
        self.batch_size = config.reason_batch_size
        self.llmcaller = config.llmcaller
        self.result_parser = ResultParser(config)

    def prompt(self, sample):
        """Create a prompt for the LLM to reason about the input_prompt."""
        sys_prompt = get_sys_prompt(sample, self.config)
    
        data_info = sample.get_data_info()
        rows, columns = sample.df.shape
        columns_list_str = sample.df_columns()
        prompt = f"""Table Path: /mnt/tmp.csv\n\nThe table data has been loaded into the variable `df`. Display the basic information of the table using `df.info`:\n {data_info}\n\nThis dataset contains {rows} rows and {columns} columns. The column names in the dataset are: {columns_list_str}\n\n Question:{sample.input_prompt}"""
        return [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ]

    def parse(self, sample, response):
        sample.generation = response
        
        sys_prompt = get_sys_prompt(sample, self.config)
        
        data_info = sample.get_data_info()
        rows, columns = sample.df.shape
        columns_list_str = sample.df_columns()
        prompt = f"""Table Path: /mnt/tmp.csv\n\nThe table data has been loaded into the variable `df`. Display the basic information of the table using `df.info`:\n {data_info}\n\nThis dataset contains {rows} rows and {columns} columns. The column names in the dataset are: {columns_list_str}\n\n Question:{sample.input_prompt}"""
        
        history = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response}
        ]
        
        sample.history = history
        self.result_parser.parse([sample], 'code')
        
        return sample
    
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
            batch_prompt = [self.prompt(sample) for sample in batch]
            try:
                responses = self.llmcaller.call_batch(batch_prompt)
                new_samples_batch = [self.parse(batch[i], responses[i]) for i in range(len(batch))]
            except Exception as e:
                print(f"An call_batch error occurred: {e}")
                continue
            new_samples.extend(new_samples_batch)
            e = time.time()
            print(f"processed {i}:{i+batch_size} / {total_rows}, used {e-s} seconds")
                
        return new_samples

    