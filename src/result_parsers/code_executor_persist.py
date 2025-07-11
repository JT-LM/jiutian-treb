import util.timeout_decorator as timeout_decorator
from result_parsers.sandboxv2 import MyBox
import re
import numpy as np
import multiprocessing
from multiprocessing import Pool
from tqdm import tqdm
import datetime

from util.str_op import has_code,filter_text


def run_test(sandbox, envs, code):
    """If test(generated_code) is not None it'll try to run the code.
    otherwise it'll just return an input and output pair.
    """
    if code is None:
        return 'run_test: code is None'
    
    try:
        
        detail_result = sandbox.run(code, envs)
        return detail_result
    except Exception as e:
        print(e)
        return str(e)

@timeout_decorator.timeout(60)
def run_test_with_timeout(sandbox, envs, code):
    """Run the test with a timeout."""
    try:
        
        info = run_test(sandbox, envs, code)
        return info
    except Exception as e:
        print(f"Exception in run_test_with_timeout: {e}")
        return f"Exception in run_test_with_timeout: {e}"

class ExecutorPersist:
    """
    A sandbox that can run python code and saves local/global variables.
    """
    def __init__(self, config=None):
        self.config = config
        self.sandboxes = {}
        
    def process_single_row(self, sample):
        try:
            code_blocks = has_code(sample.generation)

            if not code_blocks:
                return 'Does not contain code component.'
            
            last_code = code_blocks[-1]
            last_code = filter_text(last_code, '/mnt/tmp.csv')
            last_code = filter_text(last_code, 'pd.read_csv')
            last_code = filter_text(last_code, 'exit(')
            last_code = filter_text(last_code, 'import os')
            last_code = filter_text(last_code, 'import sys')
            last_code = filter_text(last_code, 'import shutil')
            last_code = filter_text(last_code, 'import pathlib')
            last_code = filter_text(last_code, 'pip install')
            last_code = filter_text(last_code, 'pip uninstall')
            last_code = filter_text(last_code, 'from os')
            last_code = filter_text(last_code, 'from sys')
            last_code = filter_text(last_code, 'from shutil')
            last_code = filter_text(last_code, 'from pathlib')
            
            sample.code = last_code
            if sample.id not in self.sandboxes:
                self.sandboxes[sample.id] = MyBox(self.config)
            sandbox = self.sandboxes[sample.id]
            
            if sample.df is not None:
                code_result = run_test_with_timeout(sandbox, {'df': sample.df}, last_code)
            else:
                code_result = run_test_with_timeout(sandbox, {}, last_code)
            sample.code_run_result = code_result
            return sample
        except Exception as e:
            print(e)
            sample.code_run_result = str(e)
            return sample
        
    def execute(self, samples):
        for i in range(len(samples)):
            sample = samples[i]
            try:
                self.process_single_row(samples[i])
            except Exception as e:
                error_message = f"Exception in execute: {e}"
                sample.code_run_result = error_message
                continue

        return samples