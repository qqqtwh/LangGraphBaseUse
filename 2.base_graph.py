''' 
1.流模式种类
graph.stream(stream_mode='...')支持多种流模式：
    values	    在图的每一步之后, 流式传输状态的完整字典{"messages":[]} (默认)
        {'messages':[HumanMessages(), AIMessage(), ToolMessage(), AIMessage()]}

    updates	    在图的每个步骤后流式传输状态更新。如果同一步骤中发生多次更新（例如，运行多个节点），则这些更新会单独流式传输。
        [
            'agent:'{'messages':[AIMessage()]},
            'tools:'{'messages':[ToolMessage()]},
            'agent:'{'messages':[AIMessage()]}
            ]
    custom	    从图节点内部流式传输自定义数据。
    messages	messages级别，可显式的看到每条消息。在任何调用 LLM 的图节点中，流式传输二元组（LLM 令牌，元数据）。
        [HumanMessages(), AIMessage(), ToolMessage(), AIMessage()]
    debug	    在图执行的整个过程中流式传输尽可能多的信息。
        [
            {'step': 1, 'timestamp': '2025-09-28T03:09:18.513146+00:00', 'type': 'task',        'payload': {'id': '4aee6887-c43b-edf6-65fa-a78e8daa7bef', 'name': 'agent', 'input': {'messages': [HumanMessage()], 'is_last_step': False, 'remaining_steps': 24}, 'triggers': ('branch:to:agent',)}}
            {'step': 1, 'timestamp': '2025-09-28T03:09:18.943151+00:00', 'type': 'task_result', 'payload': {'id': '4aee6887-c43b-edf6-65fa-a78e8daa7bef', 'name': 'agent', 'error': None, 'result': [('messages', [AIMessage()])], 'interrupts': []}}
            {'step': 2, 'timestamp': '2025-09-28T03:09:18.943783+00:00', 'type': 'task',        'payload': {'id': '6a61fcf6-8f21-acde-34cb-2ea3e51cc796', 'name': 'tools', 'input': {'__type': 'tool_call_with_context', 'tool_call': {'name': 'get_time', 'args': {}, 'id': 'chatcmpl-tool-0afe8bd8ea2f4cb88c7254828472d1f5', 'type': 'tool_call'}, 'state': {'messages': [HumanMessage(), AIMessage()}, 'triggers': ('__pregel_push',)}}
            ]

2.子图输出
for chunk in graph.stream({"foo": "foo"}, subgraphs=True)


'''

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

