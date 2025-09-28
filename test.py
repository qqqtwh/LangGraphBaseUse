
from langgraph.prebuilt import create_react_agent
from utils.llm import llm
from utils.tools import get_time,get_weather
from utils.utils import save_graph_png,smart_print_msg


# 获取工具
tools = [get_time,get_weather]

# 创建agent
agent = create_react_agent(llm, tools=tools)

# 可视化
save_graph_png(agent,'imgs/9.base_agent.png')

messages = [{"role":"user", "content":"现在几点了"}]




    
print(f"\n=== 默认 ===\n")
# invoke_res = agent.invoke({"messages": messages})
# print(invoke_res)
# for msg in invoke_res['messages']:
#     print('\n',msg)
# print(f"\n=== values ===\n")
# invoke_res = agent.invoke({"messages": messages},stream_mode='values')
# for msg in invoke_res['messages']:
#     print('\n',msg)
# print(f"\n=== updates ===\n")
# invoke_res = agent.invoke({"messages": messages},stream_mode='updates')
# for msg in invoke_res:
#     print('\n',msg)
# print(f"\n=== debug ===\n")
# invoke_res = agent.invoke({"messages": messages},stream_mode='debug')
# for msg in invoke_res:
#     print('\n',msg)

print(f"\n=== messages ===\n")
invoke_res = agent.invoke({"messages": messages},stream_mode='messages')
for msg in invoke_res:
    smart_print_msg(msg[0])