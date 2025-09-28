'''
1.父子共享状态模型: 例如父图的 foo 传递给子图的 foo
2.父子不同状态模型: 在调用子图时，将其单独封为1个节点
3.子图单独持久化


'''

from langgraph.graph import StateGraph, START
from utils.nodes import Chatbot,State
from typing_extensions import TypedDict
from utils.llm import llm

# 1.父子共享状态模型: 例如父图的 foo 传递给子图的 foo
def f1():
    class SubgraphState(TypedDict):
        foo: str  
        bar: str  

    def subgraph_node_1(state: SubgraphState):
        return {"bar": "bar"}

    def subgraph_node_2(state: SubgraphState):
        # note that this node is using a state key ('bar') that is only available in the subgraph
        # and is sending update on the shared state key ('foo')
        return {"foo": state["foo"] + state["bar"]}

    subgraph_builder = StateGraph(SubgraphState)
    subgraph_builder.add_node(subgraph_node_1)
    subgraph_builder.add_node(subgraph_node_2)
    subgraph_builder.add_edge(START, "subgraph_node_1")
    subgraph_builder.add_edge("subgraph_node_1", "subgraph_node_2")
    subgraph = subgraph_builder.compile()

    # Define parent graph
    class ParentState(TypedDict):
        foo: str

    def node_1(state: ParentState):
        return {"foo": "hi! " + state["foo"]}

    builder = StateGraph(ParentState)
    builder.add_node("node_1", node_1)
    builder.add_node("node_2", subgraph)
    builder.add_edge(START, "node_1")
    builder.add_edge("node_1", "node_2")
    graph = builder.compile()

    for chunk in graph.stream({"foo": "foo"}):
        print(chunk)

# 2.父子不同状态模型: 在调用子图时，将其单独封为1个节点
def f2():
    # 子图
    class SubgraphState(TypedDict):
        # note that none of these keys are shared with the parent graph state
        bar: str
        baz: str

    def subgraph_node_1(state: SubgraphState):
        return {"baz": "baz"}

    def subgraph_node_2(state: SubgraphState):
        return {"bar": state["bar"] + state["baz"]}

    subgraph_builder = StateGraph(SubgraphState)
    subgraph_builder.add_node(subgraph_node_1)
    subgraph_builder.add_node(subgraph_node_2)
    subgraph_builder.add_edge(START, "subgraph_node_1")
    subgraph_builder.add_edge("subgraph_node_1", "subgraph_node_2")
    subgraph = subgraph_builder.compile()

    # 父图
    class ParentState(TypedDict):
        foo: str

    def node_1(state: ParentState):
        return {"foo": "hi! " + state["foo"]}

    def node_2(state: ParentState):
        response = subgraph.invoke({"bar": state["foo"]})
        return {"foo": response["bar"]}  


    builder = StateGraph(ParentState)
    builder.add_node("node_1", node_1)
    builder.add_node("node_2", node_2)
    builder.add_edge(START, "node_1")
    builder.add_edge("node_1", "node_2")
    graph = builder.compile()

    for chunk in graph.stream({"foo": "foo"}, subgraphs=True):
        print(chunk)

# 3.子图单独持久化
def f3():
    from langgraph.checkpoint.memory import InMemorySaver
    
    # 1).统一持久化，会自动传播到子图
    subgraph_builder = StateGraph(State)
    subgraph = subgraph_builder.compile()

    graph_builder = StateGraph(State)
    graph = graph_builder.compile(checkpointer=InMemorySaver())

    # 2).子图单独持久化
    subgraph_builder = StateGraph(State)
    subgraph = subgraph_builder.compile(checkpointer=True)

    # 查看子图状态
    config = {"configurable": {"thread_id": "1"}}
    subgraph_state = graph.get_state(config, subgraphs=True).tasks[0].stat

    # 将子图的输出包含在流式输出中，在父图的 .stream() 方法中设置 subgraphs=True
    for chunk in graph.stream({"foo": "foo"},
        stream_mode="updates",
        subgraphs=True, 
    ):
        print(chunk)

if __name__ == '__main__':
    f2()
    f3()