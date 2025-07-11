from prompts.sys_prompt import get_sys_prompt
import prompts.common_prompt as common_prompt
from llm.vllmcaller import VLLMCaller,VLLMCallerConfig
import time
from sample_format.sample import Sample
from tqdm import tqdm
import pandas as pd
from result_parsers.result_parser import ResultParser
from bs4 import BeautifulSoup
import re
    

class TCoT_Reasoner(object):
    """
    The implemention of TCoT reasoning mode, where the final result is parsed from json.
    """
    def __init__(self, config):
        self.config = config
        self.batch_size = config.reason_batch_size
        self.llmcaller = config.llmcaller
        self.result_parser = ResultParser(config)

    def extract_table_content(self, sample, table_format, num_rows=50):
        if table_format == 'html':
            content = sample.Table_html[0]
            soup = BeautifulSoup(content, "html.parser")
            
            table = soup.find("table")
            if not table:
                return "No table found in the provided content."

            new_table = "<table>\n"
            thead = table.find("thead")
            if thead:
                new_table += str(thead) + "\n"

            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")[:num_rows]
                new_table += "<tbody>\n"
                for row in rows:
                    new_table += str(row) + "\n"
                new_table += "</tbody>\n"
            else:
                rows = table.find_all("tr")[:num_rows]
                for row in rows:
                    new_table += str(row) + "\n"

            new_table += "</table>"

            return new_table
        
        elif table_format == 'markdown':
            content = sample.Table_markdown[0]
            lines = content.strip().split("\n")

            table_lines = [line for line in lines if '|' in line or re.match(r'\s*-{3,}\s*', line)]
            
            try:
                extracted_lines = table_lines[:(num_rows + sample.columnslable[0] + 1)]
            except:
                extracted_lines = table_lines[:(num_rows + 2)]

            return "\n".join(extracted_lines)
        
    
    def get_TCoT_table_content(self, sample):
        table_content = ''
        if sample.df is not None and not sample.df.empty:
            rows, columns = sample.df.shape
            if rows < 50 and columns < 20:
                if self.config.mode == 'TCoT_md' and sample.Table_markdown:
                    table_content = sample.Table_markdown[0]
                elif self.config.mode == 'TCoT_html' and sample.Table_html:
                    table_content = sample.Table_html[0]
                else:
                    table_content = sample.df.to_markdown(index=False)
                return table_content
            else:
                if self.config.mode == 'TCoT_md' and sample.Table_markdown:
                    table_content = self.extract_table_content(sample, 'markdown')
                elif self.config.mode == 'TCoT_html' and sample.Table_html:
                    table_content = self.extract_table_content(sample, 'html')
                else:
                    sample.Table_markdown = [sample.df.to_markdown(index=False)]
                    table_content = self.extract_table_content(sample, 'markdown')
                return table_content
        else:
            if self.config.mode == 'TCoT_md' and sample.Table_markdown:
                table_content = sample.Table_markdown[0]
            elif self.config.mode == 'TCoT_html' and sample.Table_html:
                table_content = sample.Table_html[0]
            else:
                table_content = ""
                # print(f'{sample.id}: no table content!')
            return table_content
            

    def prompt(self, sample):
        table_content = self.get_TCoT_table_content(sample)
        
        if len(table_content) > (self.config.reason_max_model_len / 2):
            table_content = table_content[:int(self.config.reason_max_model_len / 2)] + '...'
            
        sys_prompt = get_sys_prompt(sample, self.config)
            
        return [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": sample.input_prompt  + '\n' + table_content},
        ]

    def parse(self, sample, response):
        sample.generation = response
        
        table_content = self.get_TCoT_table_content(sample)
        
        if len(table_content) > (self.config.reason_max_model_len / 2):
            table_content = table_content[:int(self.config.reason_max_model_len / 2)] + '...'
        
        sys_prompt = get_sys_prompt(sample, self.config)
        
        history = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": sample.input_prompt  + '\n' + table_content},
            {"role": "assistant", "content": response}
        ]
        sample.history = history
        self.result_parser.parse([sample], 'json')
        
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