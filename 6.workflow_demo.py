from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from utils.llm import llm
from utils.utils import save_graph_png
from langgraph.checkpoint.memory import InMemorySaver

# Graph state
class JokeState(TypedDict):
    topic: str
    joke: str
    improved_joke: str
    final_joke: str
system_prompt = {'role':'system','content':'你是一个专业的笑话编写专家，可以根据用户给出的主题或笑话进行编写,注意直接输出笑话本身内容，不要多余解释或者其他内容'}

def generate_joke(state: JokeState): # 节点: 生成初始 joke
    msg = llm.invoke([
        system_prompt,
        {'role':'user','content':f"写一个关于 {state['topic']} 的笑话]"}
    ])

    return {"joke": msg.content}

def check_punchline(state: JokeState): # 路由判断: joke 通过直接输出，失败重新生成
    if "?" in state["joke"] or "!" in state["joke"]:
        return "Pass"
    return "Fail"

def improve_joke(state: JokeState): # 节点: 在初始 joke 上提升质量
    msg = llm.invoke([
        system_prompt,
        {'role':'user','content':f"通过添加文字游戏使这个笑话更有趣: {state['joke']}"}
    ])
    return {"improved_joke": msg.content}

def polish_joke(state: JokeState):  # 节点: 打磨出最终 joke
    msg = llm.invoke([
        system_prompt,
        {'role':'user','content':f"给这个笑话增添一个令人惊讶的转折: {state['improved_joke']}"}
    ])
    return {"final_joke": msg.content}


# Build workflow
joke_workflow_build = StateGraph(JokeState)

# Add nodes
joke_workflow_build.add_node("generate_joke", generate_joke)
joke_workflow_build.add_node("improve_joke", improve_joke)
joke_workflow_build.add_node("polish_joke", polish_joke)

# Add edges to connect nodes
joke_workflow_build.add_edge(START, "generate_joke")
joke_workflow_build.add_conditional_edges(
    "generate_joke", check_punchline, {"Fail": "improve_joke", "Pass": END}
)
joke_workflow_build.add_edge("improve_joke", "polish_joke")
joke_workflow_build.add_edge("polish_joke", END)

# Compile
memory = InMemorySaver()
joke_chain = joke_workflow_build.compile(checkpointer=memory)

# Show workflow
save_graph_png(joke_chain,'imgs/8.joke.png')

# Invoke
config = {"configurable": {"thread_id": "1"}}
joke_state = joke_chain.invoke({"topic": "cats"},config=config)
print(f'--- --- --- 初始 joke:\n{joke_state["joke"]}')
if "improved_joke" in joke_state:
    print("--- --- --- 优化 joke:")
    print(joke_state["improved_joke"])
    print("--- --- --- 最终 joke:")
    print(joke_state["final_joke"])
else:
    print("joke 通过质检")