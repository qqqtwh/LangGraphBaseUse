''' agent格式

create_react_agent 构建参数：

    model:              # llm
    tools:              # tools
    *,
    prompt:             # 插入提示词模板的开头，成为system_prompt的一部分
    response_format:    # 模型响应格式
    pre_model_hook:     # 在 'agent' 节点运行前的可调用对象
    post_model_hook:    # 在 'agent' 节点运行后、tools节点之前的可调用对象
    state_schema:       # 智能体内部状态结构，存在 checkpoint/store进行持久化
    context_schema:     # 运行时外部传入的上下文，图只进行读，不进行修改，在content={}中
    checkpointer:       # 多轮对话短期记忆
    store:              # 跨会话长期记忆
    interrupt_before:   # list[str] 再执行指定节点前人工干预
    interrupt_after:    # list[str] 再执行指定节点后人工干预
    debug: bool = False,
    name: ,

invoke 调用参数：
    input: InputT | Command | None,                         # {'messages':[],'other_key':'other_value'} / Command() / None
        字符串         {"messages": "Hello"} — 被解释为一个 HumanMessage
        消息字典	   {"messages": {"role": "user", "content": "Hello"}}
        消息列表	   {"messages": [{"role": "user", "content": "Hello"}]}
        使用自定义状态  {"messages": [{"role": "user", "content": "Hello"}], "user_name": "Alice"} 
    config: RunnableConfig | None = None,                   # 运行时配置，持久化时必传
    *,
    context: ContextT | None = None,                        # 静态运行时上下文
    stream_mode: StreamMode = "values",
    print_mode: StreamMode | Sequence[StreamMode] = (),
    output_keys: str | Sequence[str] | None = None,
    interrupt_before: All | Sequence[str] | None = None,
    interrupt_after: All | Sequence[str] | None = None,
    durability: Durability | None = None,                   # 持久化策略: "sync"：每步同步持久化（安全但慢，适合金融场景）; "async"：异步持久化（默认，高性能）

输出格式：包含以下内容的字典：
    messages: 执行期间交换的所有消息列表（用户输入、助手回复、工具调用）。
    可选地，如果配置了结构化输出，则包含 structured_response。
    如果使用自定义的 state_schema，输出中也可能包含与您定义的字段相对应的其他键。这些键可以保存来自工具执行或提示逻辑的更新后状态值。
'''

from langgraph.prebuilt import create_react_agent
from utils.llm import llm
from utils.tools import get_time,get_weather
from utils.utils import save_graph_png,smart_print_msg
import asyncio

# 获取工具
tools = [get_time,get_weather]

# 创建agent
agent = create_react_agent(llm, tools=tools)

# 可视化
save_graph_png(agent,'imgs/9.base_agent.png')

messages = [{"role":"user", "content":"现在几点了"}]


async def main():
    # 3.异步完整响应
    print(f"\n=== ainvoke_res ===\n")
    ainvoke_res = await agent.ainvoke({"messages": messages})
    for msg in ainvoke_res['messages']:
        smart_print_msg(msg)

    # 4.异步流式响应
    print(f"\n=== astream_res ===\n")
    async for chunk in agent.astream({"messages": messages},stream_mode='values'):
        msg = chunk['messages'][-1]
        smart_print_msg(msg)


if __name__ == '__main__':
    
    # 1.完整响应
    print(f"\n=== invoke_res ===\n")
    invoke_res = agent.invoke({"messages": messages},config={"recursion_limit": 10})
    for msg in invoke_res['messages']:
        smart_print_msg(msg)

    # 2.流式响应, 每次响应都是当前state的完整消息
    print(f"\n=== stream_res ===\n")
    for chunk in agent.stream({"messages": messages},stream_mode='values'):
        msg = chunk['messages'][-1]
        smart_print_msg(msg)

    # 异步
    asyncio.run(main())