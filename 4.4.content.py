'''
上下文工程（Context engineering）是构建动态系统的实践，它以正确的格式提供正确的信息和工具，以便 AI 应用程序能够完成任务。上下文可以从两个关键维度进行描述：
分类：
    按可变性
        静态上下文：在执行期间不会改变的不可变数据（例如，用户元数据、数据库连接、工具）。
        动态上下文：随着应用程序运行而演变的可变数据（例如，对话历史、中间结果、工具调用观察）。
    按生命周期
        运行时上下文：作用域限定于单次运行或调用的数据。
        跨对话上下文：跨多个对话或会话持久化的数据。

LangGraph 提供了三种管理上下文的方式，结合了可变性和生命周期两个维度：
      上下文类型	                  描述	                      可变性	生命周期	        访问方法
    静态运行时上下文	       启动时传递的用户元数据、工具、数据库连接	  静态	   单次运行	     invoke/stream 的 context 参数
    动态运行时上下文（状态）	在单次运行期间演变的可变数据	         动态	  单次运行	    LangGraph 状态对象
    动态跨对话上下文（存储）	跨对话共享的持久数据                    动态	 跨对话	      LangGraph 存储

'''

from langchain_core.messages import AnyMessage
from dataclasses import dataclass
from langgraph.runtime import get_runtime
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.prebuilt import create_react_agent
from langgraph.runtime import Runtime
from utils.nodes import State
from utils.llm import llm
from utils.tools import get_time
from langchain_core.tools import tool

# 一.静态时运行上下文
@dataclass
class ContextSchema:
    user_name: str

# 节点中使用
def node(state: State, config: Runtime[ContextSchema]):
    runtime = get_runtime(ContextSchema)
    user_name = runtime.context.user_name
    
# 在工具中使用
@tool
def get_user_email() -> str:
    """Retrieve user information based on user ID."""
    runtime = get_runtime(ContextSchema)
    user_name = runtime.context.user_name

# agent中使用
def prompt(state: AgentState) -> list[AnyMessage]:
    runtime = get_runtime(ContextSchema)
    system_msg = f"You are a helpful assistant. Address the user as {runtime.context.user_name}."
    print(system_msg)
    return [{"role": "system", "content": system_msg}] + state["messages"]

agent = create_react_agent(
    model=llm,
    tools=[get_user_email],
    prompt=prompt,
    context_schema=ContextSchema
)

events = agent.invoke(
    {"messages": [{"role": "user", "content": "what is John email"}]},
    context={"user_name": "John Smith"}
)

# print(events)

# 二.动态运行时上下文(状态)
# 三.动态跨对话上下文(存储) -- 短期记忆和长期记忆
    