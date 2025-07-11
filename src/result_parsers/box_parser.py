import re
import json
from tqdm import tqdm
import util.str_op as str_op


def extract_score(input_string):
    match = re.search(r"\\boxed\{(.*?)\}", input_string)
    if match:
        return match.group(1)
    else:
        return None
    
def get_coderes_after_i(string, i):
    pattern = r"```CodeExecuteResult(?:[a-zA-Z]*)\n(.*?)```"
    matches = list(re.finditer(pattern, string, re.DOTALL))
    
    if matches:
        match = matches[-1]
        return string[match.end() + 1:]
    else:
        return ""
    
def match_boxed_content(text):
    results = []
    stack = []

    i = 0
    while i < len(text):
        if text[i:i+6] == r'boxed{':
            stack.append(i)
            i += 6
        elif text[i] == '{' and stack:
            stack.append(i)
            i += 1
        elif text[i] == '}' and stack:
            start = stack.pop()
            if len(stack) == 0:
                results.append(text[start+6:i])
            i += 1
        else:
            i += 1

    return results

def extract_answer_from_box(string):
    try:
        think, string = str_op.split_by_last_tag(string, tag="</think>")
        matches = match_boxed_content(string)
        
        # if matches and "\n".join(matches) != "":
        #     return "\n".join(matches)
        if matches and matches[-1] != "":
            return matches[-1]
        
        else:
            res = get_coderes_after_i(string, -1)
            if res != '':
                return res
            else:
                return string
            
    except Exception as e:
        print(e)
        return string


def text_result_parse(samples):
    for sample in samples:
        if sample.generation is None or sample.generation == "":
            continue
        sample.text_result = extract_answer_from_box(sample.generation)
    return samples


class BoxParser:
    """
    A parser that can parse the result from \\boxed{xxx}.
    """
    def __init__(self, config=None):
        self.config = config
        
    def execute(self, samples):
        return text_result_parse(samples)
    
    
if __name__ == '__main__':
    string = '111222\\boxed{myans}\\boxed{myans2}'
    res = extract_answer_from_box(string)
    print(res)