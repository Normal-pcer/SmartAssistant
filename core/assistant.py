"""
处理主要逻辑
"""
import json
from abc import ABC, abstractmethod
from typing import List, Callable
import os
from core.config import Config
from core.ai_client import AIClient, AITool, ChatContent
from utils.general import log, Path
from core.tools_description import EXECUTE_PYTHON_SCRIPT
from utils.file import is_text
from core.execute import execute_python_script

PREVIEW_FILE_LIMIT = 1024 * 3  # 预览 3KB 以内的文件


class Assistant:
    config: Config  # 配置文件
    selected_files: List[Path] = [] # 选中的文件

    def __init__(self) -> None:
        self.config = Config()

    def process_files(self, script: str, files: List[str], 
                      output: Callable[[str], None]) -> None:
        """
        执行 Python 脚本来处理文件。
        每次处理完文件，都会调用 output 函数，来显示提示信息。
        """
        for file in files:
            output(f"正在处理文件 {file}...\n")
            result = execute_python_script(script, file)
            output(f"程序输出：{result.stdout}\n")
            output(f"程序错误：{result.stderr}\n")

    class CommandContext(ABC):
        """
        执行用户命令的上下文。
        支持以下操作：
        - 在收到 AI 的响应时，刷新文字。
        - 在 AI 生成代码之后，确认并执行。
        """

        @abstractmethod
        def add_content(self, content: ChatContent) -> None:
            """添加新的回复内容"""
            pass

        @abstractmethod
        def confirm_script(self, script: str) -> None:
            """要求用户确认代码"""
            pass

    def execute_command(self, message: str, context: CommandContext) -> None:
        """
        执行用户的文字命令
        传入上下文进行相关响应
        """
        log.debug(f"执行用户命令: {message}")

        if 0 <= self.config.current_model_index < len(self.config.models):
            pass
        elif self.config.models:
            self.config.current_model_index = 0
            self.config.save()
            log.warning(
                f"当前模型已切换为: {self.config.models[self.config.current_model_index].name}")
        else:
            log.error("execute_command: 没有可用的模型")
            raise RuntimeError("没有可用的模型")

        model = self.config.models[self.config.current_model_index]
        tools = list[AITool]()
        if model.supports_functions:  # 允许函数调用
            def action(param: str) -> None:
                data = json.loads(param)
                script = data.get("script", "")
                if not isinstance(script, str):
                    log.error("execute_python_script: 脚本生成异常；script 参数必须是字符串")
                    return
                context.confirm_script(script)
            tools.append(AITool("execute_python_script",
                         EXECUTE_PYTHON_SCRIPT, action,))

        client = AIClient(model, tools)
        for response in client.chat_stream([
            {"role": "user", "content": message},
        ], temperature=0.2):
            context.add_content(response)  # 在客户端刷新文字

    def build_prompt(self, command: str, files: List[str], supports_fc: bool) -> str:
        """通过给定的命令和文件列表，构建 AI 提示词"""

        prompt = """
接下来将会给你一个用户的需求，你可以选择编写一个 Python 脚本并运行来解决这个任务，或者直接向用户输出文本内容。"""
        if supports_fc:
            prompt += """
如果你选择生成 Python 脚本，请通过指定的 Function Calling 工具来提交。你只能生成一个脚本，并且不能由此获得更多信息。
你可以在输出的正文中包含代码，然后在函数调用中原封不动地提交它。"""
        else:
            prompt += """
如果你选择生成 Python 脚本，请保证你的输出中仅包含一个 Python 代码块（使用 Markdown 语法 ```python [代码]``` 包裹），接下来用户将会执行这个代码。
代码块以外可以包括其他描述性的内容以帮助你输出，这些内容将会被忽略。"""

        prompt += """
Python 脚本需要遵循以下规则：
1. 可以独立地正常运行。
2. 优先使用标准库和常用依赖库。
3. 脚本必须包含 if __name__ == '__main__' 块作为程序入口。
4. 如果需要输入文件，通过 sys.argv 获取参数，第一个参数为输入文件名。
5. 如果需要输出文件，请保存为：原文件名_out.扩展名。

如果用户输入包含多个文件，你的程序将会对每个文件运行。
"""
        prompt += f"\n 用户指令：{command}"

        if files:
            prompt += "\n你需要处理以下文件："
            for file in files:
                prompt += f"\n- {file}"

                # 对于小的文本文件，添加内容预览
                if os.path.getsize(file) < PREVIEW_FILE_LIMIT and is_text(file):
                    try:
                        with open(file, 'r', encoding="utf-8") as f:
                            content = f.read()
                            prompt += f"\n文件内容：\n{content}\n"
                    except Exception as e:
                        log.warning(f"无法预览文件 {file}。原因：{e}")

        return prompt