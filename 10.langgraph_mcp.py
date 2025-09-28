# pip install langchain-mcp-adapters

from utils.llm import llm
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

llm
async def main():

    # 1.获取客户端
    client = MultiServerMCPClient(
        {
            "math": {
                "command": "python",
                "args": ["/path/to/math_server.py"],
                "transport": "stdio",
            },
            "weather": {
                "url": "https://:8000/mcp",
                "transport": "streamable_http",
            }
        }
    )
    # 2.从客户端获取tools
    tools = await client.get_tools()

    # 3.1.在智能体中使用
    agent = create_react_agent(llm,tools)
    math_response = await agent.ainvoke({"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]})
    weather_response = await agent.ainvoke({"messages": [{"role": "user", "content": "what is the weather in nyc?"}]})

    # 3.2.在工作流中使用
    model_with_tools = llm.bind_tools(tools)
    model_with_tools.invoke('')