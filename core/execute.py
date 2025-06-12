"""用于执行 Python 脚本"""

import tempfile
import subprocess
from os import unlink
from utils.general import log

class ScriptResult:
    """脚本执行结果"""
    def __init__(self, stdout: str, stderr: str, return_code: int):
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code

def execute_python_script(script: str, args: str) -> ScriptResult:
    """执行 Python 脚本"""
    log.debug(f"execute_python_script: {script}")

    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding="utf-8") as tmp:
        tmp.write(script)
        script_path = tmp.name

    result = subprocess.run(
        ["python", script_path, args],
        capture_output=True,
        text=True
    )

    unlink(script_path) #  删除临时文件

    return ScriptResult(result.stdout, result.stderr, result.returncode)
