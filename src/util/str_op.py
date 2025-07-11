import re

def split_by_last_tag(string, tag="</think>"):
    if tag in string:
        last_index = string.rfind(tag)
        before_tag = string[:last_index]
        after_tag = string[last_index + len(tag):]
        return before_tag + tag, after_tag
    else:
        return "", string

def get_code_before_i(string, i):
    pattern = r"```python(?:[a-zA-Z]*)\n(.*?)```"

    matches = list(re.finditer(pattern, string, re.DOTALL))
    
    if i < len(matches):
        match = matches[i]

        return string[:match.end()]
    else:
        return ""

def has_code(response: str) -> list:
    """Check if the response contains code blocks.

    Args:
        response (str): The text response to check

    Returns:
        list: List of code blocks found in the response
    """
    pattern = r"```python(?:[a-zA-Z]*)\n(.*?)```"
    return re.findall(pattern, response, re.DOTALL)

def filter_text(text, target_str):
    lines = text.split('\n')
    filtered_lines = [line for line in lines if target_str not in line]
    filtered_text = '\n'.join(filtered_lines)
    return filtered_text