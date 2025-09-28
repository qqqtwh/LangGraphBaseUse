


from typing import Annotated
from typing_extensions import TypedDict
from utils.llm import llm
from langgraph.graph.message import add_messages
from operator import add

# 1.Agent/Graph 的 State 定义，表示不同Agent的共享态
class State(TypedDict): # 表示Agent状态
    messages: Annotated[list, add_messages] # 所有消息为在末尾添加，而不是覆盖

class State1(TypedDict): # 表示Agent状态
    messages: Annotated[list, add_messages] # 所有消息在末尾添加，而不是覆盖
    foo: int
    bar: Annotated[list[str], add]  # 所有str在末尾添加，而不是覆盖

# 2.节点的多种定义方式
''' 输入
- **Nodes**: 图的节点:
    - 输入是上个节点类型
        - state：图的状态
        - config：一个 RunnableConfig 对象，包含配置信息，如 thread_id 和追踪信息，如 tags
        - runtime：一个 Runtime 对象，包含运行时 context 和其他信息，如 
            - store
            - stream_writer
    - 输出是包含下个节点key的字典
''' 

def chatbot(state:State):
    ai_meassage = llm.invoke(state["messages"])
    return {"messages": [ai_meassage]}

class Chatbot:
    def __init__(self,llm) -> None:
        super().__init__()
        self.llm = llm
    def __call__(self, state: State):
        ai_meassage = self.llm.invoke(state["messages"])
        return {"messages": [ai_meassage]}
    

