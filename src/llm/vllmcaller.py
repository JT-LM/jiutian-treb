from vllm import LLM, SamplingParams
import os
from transformers import AutoTokenizer
import requests, json
from tqdm import tqdm

class VLLMCallerConfig:
    def __init__(self, model_name, use_cards, llmpath, max_model_len, temperature):
        self.model_name = model_name
        self.use_cards = use_cards
        self.llmpath = llmpath
        self.max_model_len = max_model_len
        self.temperature = temperature

class VLLMCaller:
    def __init__(self, config):
        self.config = config
        os.environ["CUDA_VISIBLE_DEVICES"] = str(config.use_cards)
        
        llm_args = {
            "model": config.llmpath,
            "tensor_parallel_size": len(str(config.use_cards).split(',')),
            "max_model_len": config.max_model_len,
            "trust_remote_code": False,
            "gpu_memory_utilization": 0.9
        }
        self.llm = LLM(**{k: v for k, v in llm_args.items() if v is not None})

        self.default_sampling_params = SamplingParams(
            temperature=self.config.temperature,
            top_p=0.9,
            repetition_penalty=1.1,
            max_tokens=config.max_model_len,
            stop=None,
            n=1
        )
        
        self.tokenizer = AutoTokenizer.from_pretrained(config.llmpath)
        self.tokenizer.padding_side = 'left'
    
    def truncate_prompts_gen(self, prompts):
        truncated_prompts = []
        for prompt in prompts:
            tokenized_prompt = self.tokenizer.encode(prompt, add_special_tokens=False)
            if len(tokenized_prompt) > self.config.max_model_len:
                truncated_tokens = tokenized_prompt[:(self.config.max_model_len - 128)]
                truncated_prompt = self.tokenizer.decode(truncated_tokens, skip_special_tokens=False)
                truncated_prompts.append(truncated_prompt)
            else:
                truncated_prompts.append(prompt)
        return truncated_prompts
    
    def call(self, messages):
        prompt, think_flag = self._process_input(messages)
        prompt = self.truncate_prompts_gen([prompt])[0]
        outputs = self.llm.generate(
            prompts=[prompt],
            sampling_params=self.default_sampling_params
        )
        return self._process_output(outputs[0], think_flag)
    
    def call_batch(self, samples):
        prompts = []
        think_flags = []
        for sample in samples:
            prompt, think_flag = self._process_input(sample)
            prompts.append(prompt)
            think_flags.append(think_flag)
        # prompts = [self._process_input(sample) for sample in samples]
        prompts = self.truncate_prompts_gen(prompts)
        outputs = self.llm.generate(
            prompts=prompts,
            sampling_params=self.default_sampling_params
        )
        return [self._process_output(o, f) for o, f in zip(outputs, think_flags)]
    
    def _process_input(self, messages):
        if messages[-1]['role'] == 'assistant':
            add_generation_prompt=False
        else:
            add_generation_prompt=True
            
        try:
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=add_generation_prompt)
            if prompt.endswith('<think>\n') or prompt.endswith('<think>'):
                think_flag = True
            else:
                think_flag = False
                
        except Exception as e:
            if not self.tokenizer.chat_template:
                print("Warning: No chat template is set! use default template")
            else:
                print('Error:', e)
            self.tokenizer.chat_template = """{% for message in messages %}
<|{{ message['role'] }}|> {{ message['content'] }}{% endfor %}"""
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=add_generation_prompt)
            think_flag = False
        
        try:
            end_token = self.tokenizer.eos_token
            # print(f"End token: {end_token}")
            if prompt.endswith(f'{end_token}'):
                prompt = prompt[:-len(f'{end_token}')]
            if prompt.endswith(f'{end_token}\n'):
                prompt = prompt[:-len(f'{end_token}\n')]
        except Exception as e:
            pass
            
        # with open('debug.txt', 'a', encoding='utf-8') as f:
        #     f.write(prompt + '\n\n-------\n\n')
        return prompt, think_flag
    
    def _process_output(self, output, think_flag):
        text = output.outputs[0].text
        if think_flag:
            return '<think>\n' + text
        else:
            return text