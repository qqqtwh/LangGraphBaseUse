'''
# pip install -U "psycopg[binary,pool]" langgraph langgraph-checkpoint-postgres
# pip install -U pymongo langgraph langgraph-checkpoint-mongodb
# pip install -U langgraph langgraph-checkpoint-redis

1.短期记忆 checkpoint: 单线程智能体多轮对话
2.长期记忆 store: 多个线程跨会话存储特定数据
3.长期记忆存储与搜索
4.跨会话使用
'''

from langgraph.graph import StateGraph
from utils.nodes import State

# 一.短期记忆 checkpointer
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.checkpoint.redis import RedisSaver
from langgraph.checkpoint.memory import InMemorySaver

def f1():
    # 1.PostgresSaver
    DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        # checkpointer.setup() # 首次使用 Postgres 检查点记录器时，需要调用 checkpointer.setup()
        builder = StateGraph(State)
        graph = builder.compile(checkpointer=checkpointer)
        
    # 2.MongoDBSaver
    DB_URI = "localhost:27017"
    with MongoDBSaver.from_conn_string(DB_URI) as checkpointer:
        builder = StateGraph(State)
        graph = builder.compile(checkpointer=checkpointer)

    # 3.redis
    DB_URI = "redis://:6379"
    with RedisSaver.from_conn_string(DB_URI) as checkpointer:
        # checkpointer.setup() # 首次使用 Redis 检查点记录器时，需要调用 checkpointer.setup()
        builder = StateGraph(State)
        graph = builder.compile(checkpointer=checkpointer)

    # 4.内存中
    memory = InMemorySaver()
    graph = builder.compile(checkpointer=memory)

# 二.长期记忆store
from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres import PostgresStore
from langgraph.store.redis import RedisStore

def f2():
    # 1.内存中
    store = InMemoryStore()
    builder = StateGraph(...)
    graph = builder.compile(store=store)

    # 2.PostgresStore
    DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
    with PostgresStore.from_conn_string(DB_URI) as store:
        builder = StateGraph(...)
        graph = builder.compile(store=store)
    
    # 2.ReidsStore
    DB_URI = DB_URI = "redis://:6379"
    with RedisStore.from_conn_string(DB_URI) as store:
        builder = StateGraph(...)
        graph = builder.compile(store=store)


# 三.长期记忆会话存储与搜索
import uuid
from utils.llm import custom_elm as elm
def f3():
    from langgraph.store.memory import InMemoryStore
    in_memory_store = InMemoryStore()

    # 将长期记忆保存到命名空间
    ns_key = str(uuid.uuid4())
    in_memory_store.put(
        namespace = ("1", "2", "memories"),                     # 命名空间为元组形式，可以是任何长度
        key = ns_key,
        value = {
            'food_preference': 'I like pizza',
            'name': '小明'
            },
        index={
            "embed": elm,
            "dims": 64,
            "fields": ["food_preference", "$"]                  # "food_preference"只对value中的 "food_preference"值向量化； "$"表示对value所有都做向量化
            }
        )

    # 精确匹配搜索Item
    memories = in_memory_store.search(
        ("1", "2", "memories"), # 命名空间搜索前缀，只要是前缀相同都可以
        # query='xx' # query参数无效，仅仅是为了接口统一
        )   
    print(memories)

    # 语义搜索Item
    memories = in_memory_store.search(
        ("1", "2", "memories"),
        query="What does the user like to eat?",
        limit=3
    )
    print(memories)

    # 根据存储空间中的key查询Item
    memories = in_memory_store.get(("1", "2", "memories"),key=ns_key)
    print(memories)
    


# 四.跨会话使用：在节点中使用读取
def f4():
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.store.memory import InMemoryStore
    checkpointer = InMemorySaver()
    in_memory_store = InMemoryStore()
    graph_builder = StateGraph(State)
    graph = graph_builder.compile(checkpointer=checkpointer, store=in_memory_store)

    user_id = "1"
    config = {"configurable": {"thread_id": "1", "user_id": user_id}}

    for update in graph.stream(
        {"messages":[{"role":"user","user_id":user_id}]},
        config=config,
        stream_mode="update"
    ):
        pass

    # 例：获取信息在store中存储或搜索
    def my_node(state, config, *,store):
        # 获取信息
        user_id = config["configurable"]["user_id"]
        namespace = (user_id, "memories")
        memory_id = str(uuid.uuid4())
        # 存储
        store.put(namespace, memory_id, {"memory": memory})
        # 搜索
        memories = store.search(namespace,query=state["messages"][-1].content,
    )

if __name__ == '__main__':
    # 1.短期记忆 checkpoint 类型
    # f1()
    # 2.长期记忆 store 类型
    # f2()
    # 3.长期记忆存储与搜索
    f3()
    # 4.跨会话使用：在节点中使用读取
    # f4()


    