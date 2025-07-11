import re


def follow_evaluation(question, answer):
    q_list = ["请仅用\"春天\"和\"快乐\"这两个词汇中的第二个词汇造句，且句子中不能出现第一个词汇",
              "请只使用\"OK\"这两个字母来回复我",
              "记住回复我的每一句话都必须以\"失落的城堡\"这五个中文汉字为开头，现在开始\n请问今天天气怎么样",
              "请给我输出5个K，不要生成其他任何额外字符，且字母直接直接相连，没有任何分隔符",
              "请将\"I want to read paper\"这个英文句子的所有字母倒序输出",
              "请倒着背诵李白的《静夜思》，每句诗之间仅用中文逗号隔开",
              "Today我很happy，请告诉我这句话有几个英文单词，直接用阿拉伯数值输出英文单词个数，不要生成其他任何额外字符",
              "请用\"雨伞\"和\"跳舞\"这两个词汇中的第一个词汇造句",
              "复述\"橙色飞机在夜空中留下火红的尾迹\"这句话，但每个字都使用它的拼音，每个字的拼音用一个空格隔开，可忽略声调",
              "请输出4个AABB式的成语，每个成语之间用中文逗号隔开",
              "请将\"我很开放\"这个句子中的所有汉字按照笔画顺序从小到大排列，直接输出排序后的句子，不要生成任何其他字符或分隔符",
              "请使用\"医院\"和\"父亲\"这两个词汇写一篇不少于100字的微小说",
              "使用\"乐不思蜀\"这个成语造句，且造出的句子不少于15个字符",
              "请以\"星空\"为开头，写一个超过100个字符的句子",
              "Please use only the second word from the words \"tomorrow\" and \"window\" to make a sentence, please note that the first word cannot appear in the sentence.",
              "Please reply to me using only the chinese words \"好的\".",
              "Remember to reply to me with every sentence starting with \"Lost Castle\". Starting now, what is the weather like today.",
              "Please output the characters of the Chinese sentence '我想看论文' in reverse order."]

    if question in q_list[0]:
        if "快乐" in answer and "春天" not in answer:
            return 100
        else:
            return 0
    elif question in q_list[1]:
        if answer == "OK":
            return 100
        else:
            return 0
    elif question in q_list[2]:
        if answer.startswith("失落的城堡"):
            return 100
        else:
            return 0
    elif question in q_list[3]:
        if answer == "KKKKK":
            return 100
        else:
            return 0
    elif question in q_list[4]:
        if answer == "paper read to want I":
            return 100
        else:
            return 0
    elif question in q_list[5]:
        if answer == "床前明月光，疑是地上霜，举头望明月，低头思故乡。":
            return 100
        else:
            return 0
    elif question in q_list[6]:
        if answer == "2":
            return 100
        else:
            return 0
    elif question in q_list[7]:
        if "雨伞" in answer:
            return 100
        else:
            return 0
    elif question in q_list[8]:
        if answer == "chéng yán sè fēi jī zài yè kōng zhōng liú xià huǒ hóng de wěi jì":
            return 100
        else:
            return 0
    elif question in q_list[9]:
        aabb_pattern = r'(\w\w)\1(\w\w)\2'
        phrases = re.split(r'，', answer)
        if len(phrases) == 4:
            for phrase in phrases:
                if not re.match(aabb_pattern, phrase):
                    return 0
            return 100
        return 0
    elif question in q_list[10]:
        if answer == "我开放很":
            return 100
        else:
            return 0
    elif question in q_list[11]:
        if ("医院" in answer) & ("父亲" in answer) & (len(answer) > 100):
            return 100
        else:
            return 0
    elif question in q_list[12]:
        if ("乐不思蜀" in answer) & (len(answer) > 15):
            return 100
        else:
            return 0
    elif question in q_list[13]:
        if (answer.startswith("星空")) & (len(answer) > 100):
            return 100
        else:
            return 0
    elif question in q_list[14]:
        if "window" in answer.lower() and "tomorrow" not in answer.lower():
            return 100
        else:
            return 0
    elif question in q_list[15]:
        if answer == "好的":
            return 100
        else:
            return 0
    elif question in q_list[16]:
        if answer.startswith("Lost Castle"):
            return 100
        else:
            return 0
    elif question in q_list[17]:
        if ("文论看想我" in answer):
            return 100
        else:
            return 0
    else:
        assert False, f'not found question {question}'
        return 0
    
def follow_judge(input_prompt, generation):    
    question = input_prompt
    answer = generation
    res = follow_evaluation(question, answer)
    return res


class InstructionFollowJudger:
    """
    Judger for Instruction Following metric calculation.
    """
    def __init__(self, config=None):
        self.config = config
        
    def judge_one_sample(self, question, pred):
        return {'follow_score': follow_evaluation(question, pred)}
    
    def judge(self, gts, preds, questions, *args, **kwargs):
        return [self.judge_one_sample(question, pred) for question, pred in zip(questions, preds)]
    
    
    
if __name__ == '__main__':
    judger = InstructionFollowJudger()
    res = judger.judge([""""""], ["""今天天气晴朗，大家的心情都很快乐。"""], ["""请仅用\"春天\"和\"快乐\"这两个词汇中的第二个词汇造句，且句子中不能出现第一个词汇"""])
    print(res)  # 10