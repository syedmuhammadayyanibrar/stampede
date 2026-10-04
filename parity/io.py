import os
import json
import tempfile
import yaml
from pathlib import Path
from typing import Any, Union

def read_yaml(target_path: Union[str, Path]) -> Any:
    path = Path(target_path).resolve()
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def write_json_atomic(target_path: Union[str, Path], data: Any, indent: int = 2) -> Path:
    destination = Path(target_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    with tempfile.NamedTemporaryFile("w", dir=destination.parent, delete=False, encoding="utf-8", suffix=".tmp") as tf:
        temp_name = tf.name
        json.dump(data, tf, indent=indent)
        tf.flush()
        os.fsync(tf.fileno())

    os.replace(temp_name, destination)
    return destination

def write_text_atomic(target_path: Union[str, Path], content: str) -> Path:
    destination = Path(target_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", dir=destination.parent, delete=False, encoding="utf-8", suffix=".tmp") as tf:
        temp_name = tf.name
        tf.write(content)
        tf.flush()
        os.fsync(tf.fileno())

    os.replace(temp_name, destination)
    return destination

def read_json(target_path: Union[str, Path]) -> Any:
    path = Path(target_path).resolve()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def read_text(target_path: Union[str, Path]) -> str:
    path = Path(target_path).resolve()
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
