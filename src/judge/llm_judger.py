from llm.vllmcaller import VLLMCallerConfig, VLLMCaller
import prompts.common_prompt as prompt
from tqdm import tqdm
import re
import util.str_op as str_op

def extract_score(input_string):
    match = re.search(r"\\boxed\{(.*?)\}", input_string)
    if match:
        return match.group(1)
    else:
        return None

def llm_judge_prompt(gt, pred, question):
    """Create a prompt for the LLM to reason about the input_prompt."""
    
    return [
        {"role": "system", "content": prompt.JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": f"QUESTION: {question}\nGROUND TRUTH ANSWER: {gt}\nSTUDENT ANSWER: {pred}"},
    ]
    
def llm_judge_parse(pred, response, call_error=False):
    if '</think>' in response:
        think_content, llm_score = str_op.split_by_last_tag(response)
        llm_score = extract_score(llm_score)
    else:
        think_content = response
        llm_score = extract_score(response)
    
    if pred is None or pred == '':
        return {'LLM_score': 0, 'LLM_score_reason': 'no answer'}
    elif call_error:
        return {'LLM_score': 0, 'LLM_score_reason': 'call judge llm error'}
    else:
        try:
            if '/' in llm_score:
                llm_score = llm_score.split('/')[0]
            llm_score = float(llm_score)
            judge_reason_llm = ''
        except Exception as e:
            judge_reason_llm = f"format error, llm_score is not a number: {response}"
            llm_score = 0
        if llm_score < 0 or llm_score > 10:
            judge_reason_llm = f"llm_score out of range: {response}"
            llm_score = 0
        if judge_reason_llm == "":
            judge_reason_llm = response
            
        return {'LLM_score': llm_score, 'LLM_score_reason': judge_reason_llm}

def prompt_max_cut(batch_prompt, max_len, output_len=1024, position='left'):
    batch_prompt_cut = []
    for prompt in batch_prompt:
        length = 0
        length_without_last = 0
        for item in prompt:
            length += len(item['content'])
            length_without_last += len(item['content'])
        if length >= max_len:
            print('Warning: prompt length > max_model_len, default cut prompt')
            length_without_last -= len(prompt[-1]['content'])
            last_length = max_len - length_without_last
            if position == 'right':
                try:
                    prompt[-1]['content'] = prompt[-1]['content'][(len(prompt[-1]['content']) - last_length + output_len):]
                except Exception as e:
                    prompt[-1]['content'] = prompt[-1]['content'][(len(prompt[-1]['content']) - last_length):]
            else:
                try:
                    prompt[-1]['content'] = prompt[-1]['content'][:(last_length - output_len)]
                except Exception as e:
                    prompt[-1]['content'] = prompt[-1]['content'][:last_length]
        batch_prompt_cut.append(prompt)
    return batch_prompt_cut


class LLMJudger:
    """
    Judger for LLM score metric calculation.
    """
    def __init__(self, config=None):
        self.config = config
        self.llmcaller = config.llmcaller
        self.judge_batch_size = config.judge_batch_size
        
    def judge(self, gts, preds, questions):
        batch_size = self.judge_batch_size
        scores = []
        for i in tqdm(range(0, len(gts), batch_size)):
            batch_gts = gts[i : i + batch_size]
            batch_preds = preds[i : i + batch_size]
            batch_questions = questions[i : i + batch_size]
            
            batch_prompt = [llm_judge_prompt(batch_gts[i], batch_preds[i], batch_questions[i]) for i in range(len(batch_gts))]
            
            # batch_prompt = prompt_max_cut(batch_prompt, self.config.judge_max_model_len)
            
            try:
                responses = self.llmcaller.call_batch(batch_prompt)
            
                scores_batch = [llm_judge_parse(batch_preds[i], responses[i]) for i in range(len(batch_gts))]
            except Exception as e:
                scores_batch = [llm_judge_parse(batch_preds[i], '', call_error=True) for i in range(len(batch_gts))]
                print(f"An call_batch error occurred: {e}")
            scores.extend(scores_batch)
        return scores
    