# 保存agent可视化结构
def save_graph_png(graph, save_path="imgs/1.base.png"):
    png_data = graph.get_graph().draw_mermaid_png()
    with open(save_path, "wb") as f:
        f.write(png_data)

