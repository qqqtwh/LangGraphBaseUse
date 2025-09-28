''' 多智能体实现方式

    1.NetWork
    2.SuperVisor
    3.Hierarchical
    4.预构建方式
        supervisor: pip install langgraph-supervisor
        network: pip install langgraph-swarm

'''
from typing import Literal
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langgraph.graph import StateGraph, MessagesState, START, END


# 1.NetWork 类型：提前设定好每个agent的返回结果包含 "next_agent"
def network_agent():
    def agent_1(state: MessagesState) -> Command[Literal["agent_2", "agent_3", END]]:
        response = model.invoke(...)
        return Command(
            goto=response["next_agent"],
            update={"messages": [response["content"]]},
        )

    def agent_2(state: MessagesState) -> Command[Literal["agent_1", "agent_3", END]]:
        response = model.invoke(...)
        return Command(
            goto=response["next_agent"],
            update={"messages": [response["content"]]},
        )

    def agent_3(state: MessagesState) -> Command[Literal["agent_1", "agent_2", END]]:
        ...
        return Command(
            goto=response["next_agent"],
            update={"messages": [response["content"]]},
        )

    builder = StateGraph(MessagesState)
    builder.add_node(agent_1)
    builder.add_node(agent_2)
    builder.add_node(agent_3)

    builder.add_edge(START, "agent_1")
    network = builder.compile()

# 2.SuperVisor 类型：SuperVisorAgent决定接下来如何调用/或者将子agent作为tools
def supervisor_agent():
    def supervisor(state: MessagesState) -> Command[Literal["agent_1", "agent_2", END]]:
        response = model.invoke(...)
        return Command(goto=response["next_agent"])

    def agent_1(state: MessagesState) -> Command[Literal["supervisor"]]:
        response = model.invoke(...)
        return Command(
            goto="supervisor",
            update={"messages": [response]},
        )

    def agent_2(state: MessagesState) -> Command[Literal["supervisor"]]:
        response = model.invoke(...)
        return Command(
            goto="supervisor",
            update={"messages": [response]},
        )

    builder = StateGraph(MessagesState)
    builder.add_node(supervisor)
    builder.add_node(agent_1)
    builder.add_node(agent_2)

    builder.add_edge(START, "supervisor")

    supervisor = builder.compile()

# 3.hierarchical层级式: 最外层有1个大组长负责管理多个小组长，每个小组成管理自己的组内
def hierarchical_agent():
    class Team1State(MessagesState):
        next: Literal["team_1_agent_1", "team_1_agent_2", "__end__"]

    def team_1_supervisor(state: MessagesState) -> Command[Literal["team_1_agent_1", "team_1_agent_2", END]]:
        response = model.invoke(...)
        return Command(goto=response["next_agent"])

    def team_1_agent_1(state: MessagesState) -> Command[Literal["team_1_supervisor"]]:
        response = model.invoke(...)
        return Command(goto="team_1_supervisor", update={"messages": [response]})

    def team_1_agent_2(state: MessagesState) -> Command[Literal["team_1_supervisor"]]:
        response = model.invoke(...)
        return Command(goto="team_1_supervisor", update={"messages": [response]})

    team_1_builder = StateGraph(Team1State)
    team_1_builder.add_node(team_1_supervisor)
    team_1_builder.add_node(team_1_agent_1)
    team_1_builder.add_node(team_1_agent_2)
    team_1_builder.add_edge(START, "team_1_supervisor")
    team_1_graph = team_1_builder.compile()

    # define team 2 (same as the single supervisor example above)
    class Team2State(MessagesState):
        next: Literal["team_2_agent_1", "team_2_agent_2", "__end__"]

    def team_2_supervisor(state: Team2State):
        ...

    def team_2_agent_1(state: Team2State):
        ...

    def team_2_agent_2(state: Team2State):
        ...

    team_2_builder = StateGraph(Team2State)
    ...
    team_2_graph = team_2_builder.compile()


    # define top-level supervisor

    builder = StateGraph(MessagesState)
    def top_level_supervisor(state: MessagesState) -> Command[Literal["team_1_graph", "team_2_graph", END]]:
        response = model.invoke(...)
        # route to one of the teams or exit based on the supervisor's decision
        # if the supervisor returns "__end__", the graph will finish execution
        return Command(goto=response["next_team"])

    builder = StateGraph(MessagesState)
    builder.add_node(top_level_supervisor)
    builder.add_node("team_1_graph", team_1_graph)
    builder.add_node("team_2_graph", team_2_graph)
    builder.add_edge(START, "top_level_supervisor")
    builder.add_edge("team_1_graph", "top_level_supervisor")
    builder.add_edge("team_2_graph", "top_level_supervisor")
    graph = builder.compile()

# 4.1.预构建 supervisor
def supervisor():

    from utils.llm import llm
    from langgraph.prebuilt import create_react_agent
    from langgraph_supervisor import create_supervisor

    # agent_1
    def book_flight(from_airport: str, to_airport: str):
        """Book a flight"""
        return f"Successfully booked a flight from {from_airport} to {to_airport}."

    flight_assistant = create_react_agent(
        model=llm,
        tools=[book_flight],
        prompt="You are a flight booking assistant",
        name="flight_assistant"
    )

    # agent_2
    def book_hotel(hotel_name: str):
        """Book a hotel"""
        return f"Successfully booked a stay at {hotel_name}."
    
    hotel_assistant = create_react_agent(
        model=llm,
        tools=[book_hotel],
        prompt="You are a hotel booking assistant",
        name="hotel_assistant"
    )

    # supervisor
    supervisor = create_supervisor(
        agents=[flight_assistant, hotel_assistant],
        model=llm,
        prompt=(
            "You manage a hotel booking assistant and a"
            "flight booking assistant. Assign work to them."
        )
    ).compile()

    for chunk in supervisor.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "book a flight from BOS to JFK and a stay at McKittrick Hotel"
                }
            ]
        }
    ):
        print(chunk)
        print("\n")

# 4.2.预构建 network
def network():
    from langgraph.prebuilt import create_react_agent
    from langgraph_swarm import create_swarm, create_handoff_tool

    to_hotel_agent = create_handoff_tool(
        agent_name="hotel_assistant",
        description="Transfer user to the hotel-booking assistant.",
    )
    to_flight_agent = create_handoff_tool(
        agent_name="flight_assistant",
        description="Transfer user to the flight-booking assistant.",
    )

    flight_agent = create_react_agent(
        model="anthropic:claude-3-5-sonnet-latest",
        tools=[book_flight, to_hotel_agent],
        prompt="You are a flight booking assistant",
        name="flight_assistant"
    )
    hotel_agent = create_react_agent(
        model="anthropic:claude-3-5-sonnet-latest",
        tools=[book_hotel, to_flight_agent],
        prompt="You are a hotel booking assistant",
        name="hotel_assistant"
    )

    swarm = create_swarm(
        agents=[flight_agent, hotel_agent],
        default_active_agent="flight_agent"
    ).compile()

    for chunk in swarm.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "book a flight from BOS to JFK and a stay at McKittrick Hotel"
                }
            ]
        }
    ):
        print(chunk)
        print("\n")