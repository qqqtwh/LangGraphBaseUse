from langchain_core.tools import tool
from datetime import datetime
from pytz import timezone

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