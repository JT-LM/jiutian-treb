import jieba
from rouge_chinese import Rouge
from rouge_score import rouge_scorer

import re

def contains_chinese(text):
    pattern = re.compile(r'[\u4e00-\u9fff]')
    return bool(pattern.search(text))


class ROUGEJudger:
    """
    Judger for ROUGE metric calculation.
    """
    def __init__(self, config=None):
        self.config = config
        
    def judge_one_sample_zh(self, gt, pred):
        try:
            gt_tokenized = " ".join(jieba.cut(str(gt)))
            pred_tokenized = " ".join(jieba.cut(str(pred)))
            rouge = Rouge()
            rouge_scores = rouge.get_scores(pred_tokenized, gt_tokenized)
            return {'ROUGE': rouge_scores[0]['rouge-l']['f']}
        except Exception as e:
            print(f'ROUGE error:{e}, student answer: {pred}, ground truth answer: {gt}')
            return {'ROUGE': 0.0}
    
    def judge_one_sample_en(self, gt, pred):
        try:
            scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
            rouge_scores = scorer.score(str(gt), str(pred))
            return {'ROUGE': rouge_scores['rougeL'].fmeasure}
        except Exception as e:
            print(f'ROUGE error:{e}, student answer: {pred}, ground truth answer: {gt}')
            return {'ROUGE': 0.0}
        
    def judge(self, gts, preds, *args, **kwargs):
        scores = []
        for i in range(len(gts)):
            if contains_chinese(gts[i]):
                score = self.judge_one_sample_zh(gts[i], preds[i])
            else:
                score = self.judge_one_sample_en(gts[i], preds[i])
            scores.append(score)
        return scores
        
    
if __name__ == '__main__':
    judger = ROUGEJudger()
    gts = ["""From the data presented in the table, this cell is in the 1th column of the table, which is named 0."""]
    preds = ["""The cell with 'youthclubs' is located in column 0, and the column name is '0'."""]
    res = judger.judge(gts, preds)
    print(res)