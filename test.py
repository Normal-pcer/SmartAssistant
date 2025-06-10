from core.assistant import Assistant
from core.ai_client import ChatContent

assistant = Assistant()

full = ""

class Context(Assistant.CommandContext):
    def add_content(self, content: ChatContent) -> None:
        global full
        print(f"content({content.type}): {content.text}")
        full += content.text

    def confirm_script(self, script: str) -> None:
        print("confirm_script:", script)


assistant.execute_command(
    """生成一段 Python 代码，输出 1~10000 的所有质数或回文数。在你的回答中输出代码，同时把这段代码原封不动地通过函数调用提交。""", Context())

print(full)