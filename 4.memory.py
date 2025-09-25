# 将对话 State-messages 保存在内存中

from typing import Annotated
from typing_extensions import TypedDict
from utils.llm import llm
from utils.tools import get_time,get_weather
from langchain_core.messages import ToolMessage

from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

llm_with_tools = llm.bind_tools([get_time, get_weather])

# 保存agent可视化结构
def save_graph_png(graph, save_path="langgraph_workflow.png"):
    png_data = graph.get_graph().draw_mermaid_png()
    with open(save_path, "wb") as f:
        f.write(png_data)

# 对话主函数
config = {"configurable": {"thread_id": "1"}}
def stram_graph_update(user_input: str):
    messages = [{"role": "user", "content": user_input}]
    for event in graph.stream({"messages": messages},config=config):
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

tool_node = ToolNode(tools=[get_time,get_weather])
graph_builder.add_node('tools',tool_node)

# 3.构建图流程
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("tools","chatbot")   # 执行完 tools 节点后继续执行  chatbot 节点，相当于润色输出
graph_builder.add_conditional_edges(
    source = "chatbot",
    path = tools_condition,
)

# 4.图编译
memory = InMemorySaver()    # 内存中的检查点，实际生产中使用 SqliteSaver 或 PostgresSaver 保存在数据库中
graph = graph_builder.compile(checkpointer=memory)
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
        
        # 查看每次对话后的消息状态
        snapshot = graph.get_state(config)
        print(snapshot)

    except Exception as e:
        print(f'发生错误: {e}')
        break

