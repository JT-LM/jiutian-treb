def are_lists_equal(list1, list2):
    return len(list1) == len(list2) and all(a == b for a, b in zip(list1, list2))

def exact_match(predictions, references):
    prefixes = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    exact_match_count = 0
    total_count = len(predictions)
    for pred, ref_list in zip(predictions, references):
        count_pred = [pred.count(i) for i in prefixes]
        ref_pred = [ref_list.count(i) for i in prefixes]
        if are_lists_equal(count_pred, ref_pred):
            exact_match_count += 1
        elif pred in [ref_list]:
            exact_match_count += 1
    return exact_match_count / total_count if total_count > 0 else 0


class EMJudger:
    """
    Judger for Exact Match metric calculation.
    """
    def __init__(self, config=None):
        self.config = config
        
    def judge_one_sample(self, gt, pred):
        labels = []
        outputs = []
        labels.append(gt)
        outputs.append(pred)
        res = exact_match(outputs, labels)
        return {'EM': res}
        
    def judge(self, gts, preds, *args, **kwargs):
        return [self.judge_one_sample(gt, pred) for gt, pred in zip(gts, preds)]
        
    
    
if __name__ == '__main__':
    judger = EMJudger()
    res = judger.judge(["""表格中的信息表明，competitions所在单元格的正下方单元格内容是“eye_color”。"""], ["""eye_color"""])
    print(res)  # 1.0