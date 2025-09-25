from langchain_core.tools import tool,InjectedToolCallId
from datetime import datetime
from pytz import timezone
from langgraph.types import interrupt,Command
from langchain_core.messages import ToolMessage
from typing import Annotated

@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query}) # 模型会自动生成query输入进来
    return human_response["data"]

@tool
def custom_human_assistance(
    name: str, birthday: str, tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """Request assistance from a human."""
    human_response = interrupt(
        {
            "question": "Is this correct?",
            "name": name,
            "birthday": birthday,
        },
    )
    # If the information is correct, update the state as-is.
    if human_response.get("correct", "").lower().startswith("y"):
        verified_name = name
        verified_birthday = birthday
        response = "Correct"
    # Otherwise, receive information from the human reviewer.
    else:
        verified_name = human_response.get("name", name)
        verified_birthday = human_response.get("birthday", birthday)
        response = f"Made a correction: {human_response}"

    # This time we explicitly update the state with a ToolMessage inside
    # the tool.
    state_update = {
        "name": verified_name,
        "birthday": verified_birthday,
        "messages": [ToolMessage(response, tool_call_id=tool_call_id)],
    }
    # We return a Command object in the tool to update our state.
    return Command(update=state_update)


@tool
def get_time()->str:
    """
    查询当前时间
    Args:
    """
    try:
        tz = timezone('Asia/Shanghai')
        now = datetime.now(tz)
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")

        return current_time
    except Exception as e:
        return str(e)

@tool
def get_weather(location:str)->str:
    """
    查询输入地点的天气情况
    Args:
        location (str): 地点名称
    
    """
    return f'{location} 当前晴朗,25摄氏度,1级风速'