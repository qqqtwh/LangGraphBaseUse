from typing import Annotated
from typing_extensions import TypedDict
from utils.llm import llm
from utils.tools import get_time,get_weather
import json
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

llm_with_tools = llm.bind_tools([get_time, get_weather])

# 保存agent可视化结构
def save_graph_png(graph, save_path="langgraph_workflow.png"):
    png_data = graph.get_graph().draw_mermaid_png()
    with open(save_path, "wb") as f:
        f.write(png_data)

# 对话主函数
def stram_graph_update(user_input: str):
    messages = [{"role": "user", "content": user_input}]
    for event in graph.stream({"messages": messages}):
        for value in event.values():
            msg = value["messages"][-1]
            if msg.content and not isinstance(msg, ToolMessage):
                print("Assistant:", msg.content)

# 1.图构建初始化
class State(TypedDict):
    messages: Annotated[list, add_messages]
graph_builder = StateGraph(State)

# 2.定义并添加节点
class Chatbot: # 对话节点
    def __init__(self) -> None:
        super().__init__()
    def __call__(self, state: State):
        ai_meassage = llm_with_tools.invoke(state["messages"])
        return {"messages": [ai_meassage]}
chatbot = Chatbot()
graph_builder.add_node("chatbot",chatbot)

class BasicToolNode: # tool使用节点
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
tool_node = BasicToolNode(tools=[get_time,get_weather])
graph_builder.add_node('tools',tool_node)

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

# 3.构建图流程
graph_builder.add_edge(START, "chatbot")        # 添加起起始边 --- (START, other_node)
graph_builder.add_conditional_edges(
    source = "chatbot",                     # 该节点起始节点
    path = RouteTools(),                    # 判断节点
    path_map = {"tools":"tools", END:END}   # 节点映射
)
graph_builder.add_edge("tools","chatbot")


# 4.图编译
graph = graph_builder.compile()
# 可视化图
save_graph_png(graph)
# 5.运行graph
while True:
    try:
        user_input = input('User: ')
        if user_input.lower() in ['quit', 'exit', 'q']:
            print('对话结束')
            break
        stram_graph_update(user_input)

    except Exception as e:
        print(f'发生错误: {e}')
        break

