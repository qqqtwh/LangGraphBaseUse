''' 对话历史回溯
    state_list = graph.get_state_history(config)    获得所有迭代的 state 信息
    state = graph.get_state(config)                 获得当前的 state 信息

    可从 state_list 中获取特定 state 传入 graph.stream({"messages": messages},config=config) 使用

'''
from utils.utils import save_graph_png
from utils.llm import llm
from utils.tools import get_time,get_weather
from langchain_core.messages import ToolMessage

from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver

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
memory = InMemorySaver()    # 内存中的检查点，实际生产中使用 SqliteSaver 或 PostgresSaver 保存在数据库中
graph = graph_builder.compile(checkpointer=memory)
# 可视化图
save_graph_png(graph,'imgs/7.png')
# 5.运行graph
config = {"configurable": {"thread_id": "1"}} # 固定字段

while True:
    try:
        user_input = input('User: ')
        if user_input.lower() in ['quit', 'exit', 'q']:
            print('对话结束')
            break
        elif user_input.lower() in ['history']:
            
            for state in graph.get_state_history(config):
                # print("-" * 80)
                # print(f"Num Messages: {len(state.values['messages'])}, Next: {state.next}, Config: {state.config}")
                if len(state.values["messages"]) == 6: # 自定义条件需要回溯的 state
                    config = state.config
                    break
            continue
        messages = [
            {"role": "system", "content": "你是一个通用博学，乐于助人的AI助手，可以积极回答用户问题"},
            {"role": "user", "content": user_input}
            ]
        for event in graph.stream({"messages": messages},config=config):
            for value in event.values():
                msg = value["messages"][-1]
                if msg.content and not isinstance(msg, ToolMessage):
                    print("Assistant:", msg.content)
        print('=====')
        for i in [i.content for i in graph.get_state(config).values['messages']]:
            print(i)
        print('---')
    except Exception as e:
        print(f'发生错误: {e}')
        break

