# 将对话 State 通过Config 以快照的形式保存在内存中
''' 
通过 config = {"configurable": {"thread_id": "1"}} 来设置状态state在内存中的唯一性

# 1.获取 snapshot
通过 snapshot = graph.get_state(config) 或 snapshots =  graph.get_state_history(config) 获得当前完整快照状态

StateSnapshot(
    # 在此时间点的状态通道的值。
    values={'foo': 'b', 'bar': ['a', 'b']},
    
    # 一个元组，包含图中接下来要执行的节点名称
    next=(),

    # 与此检查点关联的配置
    config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28fe-6528-8002-5a559208592c'}},

    # 与此检查点关联的元数据
    metadata={'source': 'loop', 'writes': {'node_b': {'foo': 'b', 'bar': ['b']}}, 'step': 2},

    created_at='2024-08-29T19:19:38.821749+00:00',
    
    # 一个PregelTask对象的元组，包含有关接下来要执行的任务的信息。如果该步骤之前尝试过，它将包含错误信息。如果图在节点内部被动态中断，任务将包含与中断相关的额外数据。
    parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f9-6ec4-8001-31981c2c39f8'}}, tasks=()
)

# 2.replay
    config = {"configurable": {"thread_id": "1", "checkpoint_id": "0c62ca34-ac19-445d-bbb0-5b4984975b2a"}}
    graph.invoke(None, config=config)

# 3.更行图状态
    graph.update_state(config, {"foo": 2, "bar": ["b"]})

'''


from utils.utils import save_graph_png,smart_print_msg
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
save_graph_png(graph,'imgs/4.png')
# 5.运行graph
config = {"configurable": {"thread_id": "1"}} # 固定字段
while True:
    try:
        user_input = input('User: ')
        if user_input.lower() in ['quit', 'exit', 'q']:
            print('对话结束')
            break
    
        messages = [{"role": "user", "content": user_input}]
        for event in graph.stream({"messages": messages},config=config):
            for value in event.values():
                msg = value["messages"][-1]
                smart_print_msg(msg)
        
        # 查看每次对话后的消息状态
        snapshot = graph.get_state(config)
        # print(snapshot)

    except Exception as e:
        print(f'发生错误: {e}')
        break

