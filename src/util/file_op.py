import json
import os
import yaml
import random

def is_safe_path(path):
    """
    Check if the path is a safe path.
    :param path: The path to be checked.
    :return: True if the path is safe, otherwise False.
    """
    
    base_dirs = [
        os.path.abspath(os.path.join(os.getcwd(), '../config')),
        os.path.abspath(os.path.join(os.getcwd(), "../eval_log/")),
        os.path.abspath(os.path.join(os.getcwd(), "../eval_output/"))
    ]
    
    # Normalize the path to prevent path traversal attacks
    normalized_path = os.path.abspath(os.path.normpath(path))
    
    # Check if the path starts with base_dir
    for base_dir in base_dirs:
        if normalized_path.startswith(base_dir):
            return True
    
    return False

def read_dict_from_jsonl(path):
    if not is_safe_path(path):
        raise ValueError(f"Unsafe path: {path}, Sorry, for security reasons, we only allow the program to access files in specific directories. If needed, you can modify the `is_safe_path` function in `file_op.py`.")
    data = []
    with open(path, 'r', encoding='utf-8') as file:
        for line in file:
            json_obj = json.loads(line.strip())
            data.append(json_obj)
    return data

def read_dict_from_json(path):
    if not is_safe_path(path):
        raise ValueError(f"Unsafe path: {path}, Sorry, for security reasons, we only allow the program to access files in specific directories. If needed, you can modify the `is_safe_path` function in `file_op.py`.")
    with open(path,'r', encoding='utf-8') as f:
        data=json.load(f)
    return data

def read_dict_from_yaml(path):
    if not is_safe_path(path):
        raise ValueError(f"Unsafe path: {path}, Sorry, for security reasons, we only allow the program to access files in specific directories. If needed, you can modify the `is_safe_path` function in `file_op.py`.")
    with open(path, "r", encoding='utf-8') as f:
        return yaml.safe_load(f)

def read_lines_from_file(path):
    if not is_safe_path(path):
        raise ValueError(f"Unsafe path: {path}, Sorry, for security reasons, we only allow the program to access files in specific directories. If needed, you can modify the `is_safe_path` function in `file_op.py`.")
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    return lines
    
def save_objects(objects, path):
    if not is_safe_path(path):
        raise ValueError(f"Unsafe path: {path}, Sorry, for security reasons, we only allow the program to access files in specific directories. If needed, you can modify the `is_safe_path` function in `file_op.py`.")
    mkdir(path)
    if path.endswith('.json'):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(objects, f, ensure_ascii=False, indent=4)
    else:
        with open(path, "w", encoding="utf-8") as f:
            for obj in objects:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
              
            
def list_files(directory):
    paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if 'ipynb_checkpoints' in file_path:
                continue
            paths.append(file_path)
    return paths


def mkdir(path):
    if '.' in os.path.basename(path):
        folder_path = os.path.dirname(path)
    else:
        folder_path = path

    if folder_path == '':
        return
    os.makedirs(folder_path, exist_ok=True)
    
def sample_lines(input_file, output_file, sample_ratio=None, sample_num=None, random_sampling=True):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if sample_num is not None:
        sample_size = sample_num
    elif sample_ratio is not None:
        sample_size = int(len(lines) * sample_ratio)
    else:
        assert False, f'sample_ratio and sample_num both are none'

    if random_sampling:
        if sample_size > len(lines):
            print(f'{input_file} has {len(lines)} lines, not enough for {sample_size}')
            sampled_lines = lines
        else:
            sampled_lines = random.sample(lines, sample_size)
    else:
        sorted_data = sorted(lines, key=lambda x: len(str(x)))
        sampled_lines = sorted_data[:sample_size]

    with open(output_file, 'w', encoding='utf-8') as f:
        for line in sampled_lines:
            f.write(line)
            
            
def combine_jsonl(files, ofilepath):
    total_data = []
    for file in files:
        data = read_dict_from_jsonl(file)
        total_data.extend(data)
    print('combined', len(total_data), 'samples')
    save_objects(total_data, ofilepath)