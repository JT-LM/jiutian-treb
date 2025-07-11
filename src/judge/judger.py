from judge.BLEU_judger import BLEUJudger
from judge.EM_judger import EMJudger
from judge.instruction_follow_judger import InstructionFollowJudger
from judge.llm_judger import LLMJudger
from judge.ROUGE_judger import ROUGEJudger


judger_map = {
    'BLEU': BLEUJudger,
    'EM': EMJudger,
    'Instruction_Following': InstructionFollowJudger,
    'LLM_score': LLMJudger,
    'ROUGE': ROUGEJudger
}
judgers = {}


class Judger:
    """
    Judger Interface that calculates different metrics according to targeting metrics based on predifined judger classes.
    """
    def __init__(self, config=None):
        self.config = config
        self.metrics = config.metrics
        self.mode = config.mode
        
        self.judgers = {}
        for metric in self.metrics:
            if metric not in judgers:
                judgers[metric] = judger_map[metric](config)
            self.judgers[metric] = judgers[metric]
        
    def judge(self, samples):
        llm_anss = []
        for sample in samples:
            if 'PoT' in self.mode:
                llm_ans = sample.code_run_result
            else:
                llm_ans = sample.text_result
            llm_anss.append(llm_ans)
        
        questions = []
        for sample in samples:
            question = sample.input_prompt
            questions.append(question)
        
        for metric in self.metrics:
            gts = []
            for sample in samples:
                gt = sample.answer
                gts.append(gt)
            
            metric_judger = self.judgers[metric]
            infos = metric_judger.judge(gts, llm_anss, questions)

            for sample, info in zip(samples, infos):
                sample.judge_scores.update(info)
        
        return samples