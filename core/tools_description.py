"""
允许 AI 进行调用的工具描述
"""
from typing import Dict, Any

EXECUTE_PYTHON_SCRIPT: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "execute_python_script",
        "description": "Execute a Python script to process files",
        "parameters": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "The Python script code to execute"
                }
            },
            "required": ["script"]
        }
    }
}
