import re
import json
from tqdm import tqdm
import util.str_op as str_op


def extract_answer_from_json(string):
    think, string = str_op.split_by_last_tag(string, tag="</think>")
    try:
        json_pattern = r"```json\s*([\s\S]*?)\s*```"
        matches = re.findall(json_pattern, string, re.DOTALL)
        
        if not matches:
            return string
        
        match = matches[-1]
        json_obj = json.loads(match)

        if "answer" in json_obj:
            return str(json_obj["answer"])
        else:
            return string
    except Exception as e:
        return string


def text_result_parse(samples):
    for sample in samples:
        if sample.generation is None or sample.generation == "":
            continue
        sample.text_result = extract_answer_from_json(sample.generation)
    return samples


class TextResultParser:
    """
    A parser that can parse the result from json.
    """
    def __init__(self, config=None):
        self.config = config
        
    def execute(self, samples):
        return text_result_parse(samples)