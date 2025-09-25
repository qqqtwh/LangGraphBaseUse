from langgraph.graph import StateGraph, START, END
from utils.utils import save_graph_png
from utils.llm import llm

# 1.图构建初始化
from utils.nodes import State
graph_builder = StateGraph(State)

# 2.定义并添加节点，比如聊天节点
from utils.nodes import Chatbot
graph_builder.add_node("chatbot", Chatbot(llm))      # 添加节点 --- 聊天节点

# 3.添加图流程边结构
graph_builder.add_edge(START, "chatbot")        # 添加起起始边 --- (START, other_node)
graph_builder.add_edge("chatbot", END)          # 添加结束边 --- (other_node, END)

# 4.图编译
graph = graph_builder.compile()
# 可视化图
save_graph_png(graph,'imgs/1.base.png')

# 5.运行graph
while True:
    try:
        user_input = input('User: ')
        if user_input.lower() in ['quit', 'exit', 'q']:
            print('对话结束')
            break

        for event in graph.stream(input={"messages": [{"role": "user", "content": user_input}]}):
            for value in event.values():
                print("Assistant:", value["messages"][-1].content)

    except Exception as e:
        print(f'发生错误: {e}')
        break

