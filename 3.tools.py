from utils.utils import save_graph_png
from utils.llm import llm
from utils.tools import get_time,get_weather
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.graph import StateGraph, START

current_tools = [get_time, get_weather]

# 1.图构建初始化
from utils.nodes import State
graph_builder = StateGraph(State)

# 2.定义并添加节点
from utils.nodes import Chatbot
llm_with_tools = llm.bind_tools(current_tools)
chatbot = Chatbot(llm_with_tools)
graph_builder.add_node("chatbot",chatbot)

tool_node = ToolNode(tools=current_tools)
graph_builder.add_node('tools',tool_node)

# 3.构建图流程
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("tools","chatbot")   # 执行完 tools 节点后继续执行  chatbot 节点，相当于润色输出
graph_builder.add_conditional_edges(
    source = "chatbot",
    path = tools_condition,
)

# 4.图编译
graph = graph_builder.compile()
# 可视化图
save_graph_png(graph,'imgs/3.png')
# 5.运行graph
while True:
    try:
        user_input = input('User: ')
        if user_input.lower() in ['quit', 'exit', 'q']:
            print('对话结束')
            break
        messages = [{"role": "user", "content": user_input}]
        for event in graph.stream({"messages": messages}):
            for value in event.values():
                msg = value["messages"][-1]
                if msg.content and not isinstance(msg, ToolMessage):
                    print("Assistant:", msg.content)

    except Exception as e:
        print(f'发生错误: {e}')
        break

