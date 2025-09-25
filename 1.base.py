from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from utils.llm import llm

# 保存agent可视化结构
def save_graph_png(graph, save_path="imgs/1.base.png"):
    png_data = graph.get_graph().draw_mermaid_png()
    with open(save_path, "wb") as f:
        f.write(png_data)
# 对话主函数
def stram_graph_update(user_input: str):
    messages = [
        {"role": "user", "content": user_input}
    ]
    for event in graph.stream({"messages": messages}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

# 1.图构建初始化
class State(TypedDict): # 表示Agent状态
    messages: Annotated[list, add_messages] # 所有消息为在末尾添加，而不是覆盖
graph_builder = StateGraph(State)

# 2.定义并添加节点，比如聊天节点
def chatbot(state: State):
    # 节点返回类型必须是字典，其key必须是State中定义的字段
    return {"messages": [llm.invoke(state["messages"])]}
graph_builder.add_node("chatbot", chatbot)      # 添加节点 --- 聊天节点

# 3.添加图流程边结构
graph_builder.add_edge(START, "chatbot")        # 添加起起始边 --- (START, other_node)
graph_builder.add_edge("chatbot", END)          # 添加结束边 --- (other_node, END)

# 4.图编译
graph = graph_builder.compile()
# 可视化图
# save_graph_png(graph)

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

