from langchain_core.messages import AIMessage,HumanMessage,ToolMessage

# 保存agent可视化结构
def save_graph_png(graph, save_path="imgs/1.base.png"):
    png_data = graph.get_graph().draw_mermaid_png()
    with open(save_path, "wb") as f:
        f.write(png_data)

def smart_print_msg(msg):
    if isinstance(msg,HumanMessage) and msg.content:
        print(f'User: {msg.content}')
    elif isinstance(msg,AIMessage):
        if msg.content:
            print(f'AI: {msg.content}')
        elif msg.tool_calls:
            print(f'AI: 准备调用工具{msg.tool_calls}')
        else:
            print(f'AI: 回复为空/无工具调用 {msg}')
    else:
        print(f'Tool: {msg.content}')