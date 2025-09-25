from langchain_openai import ChatOpenAI
from openai import OpenAI
from typing import List
from langchain_core.embeddings import Embeddings
from dotenv import load_dotenv
import os
load_dotenv()

api_key=os.getenv('api_key')
base_url=os.getenv('base_url')
model_name=os.getenv('model_name')
vision_model=os.getenv('vision_model')
multi_model=os.getenv('multi_model')
embedding_model=os.getenv('embedding_model')

llm = ChatOpenAI(base_url=base_url,api_key=api_key,model=model_name)
vlm = ChatOpenAI(base_url=base_url,api_key=api_key,model=vision_model)
mlm = ChatOpenAI(base_url=base_url,api_key=api_key,model=multi_model,streaming=True)


class ParrotLinkEmbeddings(Embeddings):
    def __init__(self,model:str=embedding_model):
        self.model = model
        self.client = OpenAI(base_url=base_url,api_key=api_key)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        res = self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=64, # 向量维度 64, 128, 256, 512, 768, 1024
            encoding_format="float"
        )
        return [i.embedding for i in res.data] 

    def embed_query(self, text: str) -> list[float]:        
        return self.embed_documents([text])[0]

elm = ChatOpenAI(base_url=base_url,api_key=api_key,model=embedding_model)