from io import StringIO
import pandas as pd
import json
import re
import pandas as pd
pd.set_option('display.width', None)
pd.set_option('display.max_columns',None)
import util.file_op as op
from typing import List, Dict

import os

pid = os.getpid()

def markdown_to_df(markdown_str):
    lines = markdown_str.strip().split('\n')
    
    header = lines[0]
    columns = [col.strip() for col in header.split('|')[1:-1]]
    
    data_rows = lines[2:]
    data = []
    for row in data_rows:
        row_data = [cell.strip() for cell in row.split('|')[1:-1]]
        data.append(row_data)

    df = pd.DataFrame(data, columns=columns)
    df.to_csv(f'./tmp/{pid}_tmp.csv', index=False)
    df = pd.read_csv(f'./tmp/{pid}_tmp.csv')
    return df

class Sample:
    """
    The Entity class that saves necessary information for reasoning a table question.
    """
    def __init__(self,
                 # The following fields correspond to the fields in the dataset.
                 id: str,
                 file_path:List[str],
                 instruction:str,
                 question:str,
                 answer:str,
                 title:List[str],
                 columnslable: List[int],
                 Table_markdown: List[str],
                 Table_html: List[str],
                 number_answer: float,
                 
                 # The following are fields related to model inference.
                 mode=None,
                 df=None,
                 input_prompt='',
                 history='',
                 generation='',
                 text_result = '',
                 code='',
                 code_run_result='',
                 
                 # The following are fields related to evaluation scores.
                 judge_scores=None,
                 add_info=None):
        self.id = id
        self.file_path = file_path
        self.instruction = instruction
        self.question = question
        self.answer = str(answer)
        self.title = title
        self.columnslable = columnslable
        self.Table_markdown = Table_markdown
        self.Table_html = Table_html
        self.number_answer = number_answer
        
        self.mode = mode
        self.df = df
        
        self.input_prompt = input_prompt
        self.history = history
        self.generation = generation
        self.text_result = text_result
        self.code = code
        self.code_run_result = code_run_result
        
        self.judge_scores = judge_scores if judge_scores is not None else {}
        self.add_info = add_info if add_info is not None else {}
        
    def __str__(self):
        return str(vars(self))
    
    def __repr__(self):
        return str(vars(self))
        
    def prompt(self):
        pass
    
    def df_preprocess(self):
        # Column name processing
        if self.columnslable[0] > 0:
            try:
                self.df.columns = self.df.columns.str.strip()
                self.df = self.df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            except Exception as e:
                print(f'Column name processing error: {e}, Data ID: {self.id}')
        
        # Null value processing
        # try: 
        #     for column in self.df.columns:
        #         if self.df[column].isnull().all():
        #             self.df[column].fillna('nan', inplace=True)
        #         elif pd.api.types.is_numeric_dtype(self.df[column]):
        #             self.df[column].fillna(0, inplace=True)
        #         elif pd.api.types.is_string_dtype(self.df[column]):
        #             self.df[column].fillna('nan', inplace=True)
        # except Exception as e:
        #     print(f'Null value processing error: {e}, Data ID: {self.id}')
    
    def df_info(self):
        output = StringIO()
        self.df.info(memory_usage=False, buf=output)
        info_str = output.getvalue()
        return info_str
    
    def df_columns(self):
        return str(self.df.columns.tolist())
    
    def df_head(self, n_lines=10):
        return str(self.df.head(n_lines))
    
    def df_markdown(self):
        return self.df.to_markdown(index=False)
    
    def df_content(self):
        rows, columns = self.df.shape

        if rows < 50 and columns < 20:
            # For small datasets (fewer than 50 rows and 20 columns), display all data
            print_1 = 'Full dataset contents:'
            print_2 = self.df.to_csv(sep='\t', na_rep='nan')
        else:
            # For larger datasets, display the first 10 rows
            print_1 = 'First 10 rows of the dataset:'
            print_2 = self.df.head(10).to_csv(sep='\t', na_rep='nan')
        info = f"""{print_1}
        {print_2}"""
        return info
    
    def get_data_info(self):
        info_str = self.df_info()
        info_table = self.df_content()
        
        data_info = f"""Basic dataset information:
{info_str}
{info_table}"""
        
        return data_info
        
    
    def to_json(self):
        info = vars(self).copy()
        try:
            if info['df'] is not None and not info['df'].empty:
                info['df'] = info['df'].to_markdown(index=False)
            else:
                info['df'] = ""
        except Exception as e:
            info['df'] = "df.to_markdown error, default empty"
        return info
    
    @staticmethod
    def load_from_dict(d, config):
        sample = Sample(**d)
        sample.mode = config.mode

        if sample.file_path is not None and len(sample.file_path) > 0 and sample.file_path[0] != "":
            if sample.columnslable[0] > 0:
                sample.df = pd.read_csv(sample.file_path[0], header=[i for i in range(sample.columnslable[0])])
            else:
                sample.df = pd.read_csv(sample.file_path[0], header=None)
        elif len(sample.Table_markdown) > 0 and sample.Table_markdown[0] != "":
            sample.df = markdown_to_df(sample.Table_markdown[0])
        else:
            sample.df = None
        
        if sample.df is not None:
            sample.df_preprocess()
            
        sample.input_prompt = ''
        if config.if_instruction and sample.instruction != "":
            sample.input_prompt += f'{sample.instruction}\n'
            
        sample.input_prompt += sample.question
        
        if config.if_title:
            title = "\n".join(sample.title)
            sample.input_prompt += f'\n{title}'
        
        return sample
    
    @staticmethod
    def save_samples(samples, save_path):
        if not op.is_safe_path(save_path):
            raise ValueError(f"Unsafe path: {save_path}, Sorry, for security reasons, we only allow the program to access files in specific directories. If needed, you can modify the `is_safe_path` function in `file_op.py`.")
        with open(save_path, "w", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample.to_json(), ensure_ascii=False) + "\n")
    
    @staticmethod
    def save_samples_a(samples, save_path):
        if not op.is_safe_path(save_path):
            raise ValueError(f"Unsafe path: {save_path}, Sorry, for security reasons, we only allow the program to access files in specific directories. If needed, you can modify the `is_safe_path` function in `file_op.py`.")
        with open(save_path, "a", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample.to_json(), ensure_ascii=False) + "\n")
                
    @staticmethod
    def load_samples(path, config):
        if path.split('.')[-1] == 'json':
            samples = op.read_dict_from_json(path)
        elif path.split('.')[-1] == 'jsonl':
            samples = op.read_dict_from_jsonl(path)
        else:
            pass
        samples = [Sample.load_from_dict(sample, config) for sample in samples]
        return samples
        