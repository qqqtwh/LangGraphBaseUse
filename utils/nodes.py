from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage
import json
from langgraph.graph import END

class State(TypedDict): # 表示Agent状态
    messages: Annotated[list, add_messages] # 所有消息为在末尾添加，而不是覆盖

class CustomState(TypedDict):
    messages: Annotated[list, add_messages]
    name: str
    birthday: str


 # 对话节点
class Chatbot:
    def __init__(self,llm) -> None:
        super().__init__()
        self.llm = llm
    def __call__(self, state: State):
        ai_meassage = self.llm.invoke(state["messages"])
        return {"messages": [ai_meassage]}

class ChatbotWithHuman:
    # 添加人为干预
    def __init__(self,llm) -> None:
        super().__init__()
        self.llm = llm
    def __call__(self, state: State):
        ai_meassage = self.llm.invoke(state["messages"])
        assert len(ai_meassage.tool_calls) <=1 # 在需要人工干预的场景中，强制ai使用0或1个工具
        return {"messages": [ai_meassage]}

 # tool使用节点
class BasicToolNode:
    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name:tool for tool in tools}
    def __call__(self, state:State):
        messages = state.get('messages',[])
        if messages:
            message = messages[-1]
        else:
            raise ValueError("input 中没有 message")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call['name']].invoke(tool_call['args'])
            outputs.append(ToolMessage(
                content=json.dumps(tool_result,ensure_ascii=False),
                name=tool_call['name'],
                tool_call_id = tool_call['id']
            ))
        return {"messages": outputs}
    

# 条件边判断节点：根据 ai_meassage 结果判断，接下来走tools节点还是END节点
class RouteTools:
    def __init__(self) -> None:
        super().__init__()
    def __call__(self,state: State):
        if isinstance(state, list):
            ai_meassage = state[-1]
        elif messages := state.get("messages", []):
            ai_meassage = messages[-1]
        else:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")
        if hasattr(ai_meassage, "tool_calls") and len(ai_meassage.tool_calls) > 0:
            return "tools"
        return END