"""
和 AI 交互
"""
import openai
from typing import List, Callable, Dict, Any, Optional
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from enum import Enum


class AIModel:
    """AI 模型信息"""
    name: str
    model_id: str
    api_base: str
    api_key: str
    supports_functions: bool

    def __init__(self, name: str, model_id: str, api_base: str, 
                 api_key: str, supports_functions: bool = False) -> None:
        self.name = name
        self.model_id = model_id
        self.api_base = api_base
        self.api_key = api_key
        self.supports_functions = supports_functions
    
    def to_dict(self) -> Dict[str, str | bool]:
        return self.__dict__


class AITool:
    """
    工具信息

    调用时需要在 action 中传入一个 JSON 形式的参数
    """
    name: str
    info: Dict[str, Any]
    action: Callable[[str], None]

    def __init__(self, name: str, info: Dict[str, Any], action: Callable[[str], None]) -> None:
        self.name = name
        self.info = info
        self.action = action

    def call(self, params: str) -> None:
        self.action(params)


example_model = AIModel("Example Model", "example", "https://api.example.com/v1", "")

class ChatContent:
    """AI 返回的聊天内容"""
    class Type(Enum):
        REASONING = "reasoning" # 推理内容
        CONTENT = "content" # 常规内容
        TOOL_ARGUMENT = "tool_argument" # 工具参数
    
    type: Type
    text: str

    def __init__(self, type: Type, text: str) -> None:
        self.type = type
        self.text = text

class AIClient:
    """AI 模型客户端"""
    model: AIModel
    client: openai.OpenAI
    tools: Dict[str, AITool]  # 名称到工具的映射

    def __init__(self, model: AIModel, tools: Optional[List[AITool]] = None) -> None:
        tools = tools or []
        self.model = model
        self.client = openai.OpenAI(
            api_key=model.api_key, base_url=model.api_base)
        self.tools = {tool.name: tool for tool in tools}

    

    def chat_stream(self, messages: List[ChatCompletionMessageParam],
                    temperature: float = 0.2):  # -> Generator
        """流式调用，返回生成器"""
        openai_tools = [ChatCompletionToolParam(
            **tool.info) for _, tool in self.tools.items()]
        stream = self.client.chat.completions.create(
            model=self.model.model_id,
            messages=messages,
            tools=openai_tools,
            tool_choice="auto",
            stream=True,
            temperature=temperature,
        )

        full_response = ""

        class ToolCall:
            id: str
            name: str
            args: str

            def __init__(self, id: str, name: str, args: str) -> None:
                self.id = id
                self.name = name
                self.args = args

        tool_call_buf = dict[int, ToolCall]()

        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta

                # 文本内容
                if delta.content:
                    full_response += delta.content
                    yield ChatContent(ChatContent.Type.CONTENT, delta.content)

                # 推理内容
                if hasattr(delta, "reasoning_content"):
                    content = getattr(delta, "reasoning_content")
                    if isinstance(content, str):
                        yield ChatContent(ChatContent.Type.REASONING, content)

                
                # 工具调用
                if delta.tool_calls:
                    for call in delta.tool_calls:
                        index = call.index
                        function = call.function
                        if function is None:
                            continue
                        if index not in tool_call_buf:
                            tool_call_buf[index] = ToolCall(
                                id=call.id or "",
                                name=function.name or "",
                                args=function.arguments or ""
                            )
                        else:  # 追加参数
                            tool_call_buf[index].args += function.arguments or ""
                        if function.arguments is not None:
                            yield ChatContent(ChatContent.Type.TOOL_ARGUMENT, function.arguments)

        # 依次进行工具调用
        for tool_call in tool_call_buf.values():
            if tool_call.name not in self.tools:
                raise ValueError(f"Unknown tool: {tool_call.name}")
            tool = self.tools[tool_call.name]
            tool.call(tool_call.args)
