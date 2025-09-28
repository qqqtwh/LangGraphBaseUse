
''' 在agent中加入人为干预

def some_node_inside_alice(state):
    return Command(
        goto="bob",
        update={"my_state_key": "my_state_value"}, # 子图、父图、全剧图均更新
        graph=Command.PARENT,   # goto要去的节点不在当前图中，在父图中； Command.CURRENT（默认）/ Command.ROOT
    )


'''

import os,sys
os.chdir(sys.path[0])

from utils.llm import llm
from utils.utils import save_graph_png
from langchain_core.messages import ToolMessage,HumanMessage,AIMessage
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver

from utils.tools import get_time,get_weather,human_assistance
from langgraph.types import Command


current_tools = [get_time, get_weather,human_assistance]
llm_with_tools = llm.bind_tools(current_tools)

# 1.图构建初始化
from utils.nodes import State
graph_builder = StateGraph(State)

# 2.定义并添加节点
from utils.nodes import ChatbotWithHuman
llm_with_tools = llm.bind_tools(current_tools)
chatbot = ChatbotWithHuman(llm_with_tools)
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
save_graph_png(graph,'imgs/5.png')

# 5.运行graph
config = {"configurable": {"thread_id": "1"}}
# 我需要去询问管理员协助,告诉我如何打开库房的门
# 先按第1个按钮，再按第2个按钮就行

while True:
    try:
        
        user_input = input('User: ')
        if user_input.lower() in ['quit', 'exit', 'q']:
                print('对话结束')
                break

        events = graph.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config,
            stream_mode="values",
        )
        for event in events:
            if "messages" in event:
                msg = event["messages"][-1]
                if isinstance(msg,HumanMessage) and msg.content:
                    pass
                    # print(f'User: {msg.content}')
                if isinstance(msg,AIMessage):
                    if msg.content: # 回答
                        print(f'Assistant: {msg.content}')
                    else: # 调用工具
                        if msg.tool_calls[-1]['name'] == 'human_assistance':
                            human_input = input('专家: ')
                            human_command = Command(resume={"data": human_input})
                            # 使用 Command恢复执行
                            for event in graph.stream(human_command, config, stream_mode="values"):
                                if "messages" in event:
                                    msg = event["messages"][-1]
                                    if isinstance(msg,AIMessage) and msg.content:
                                        print(f'Assistant: {msg.content}')
  
    except Exception as e:
        print(f'发生错误: {e}')
        break
    

