"""
RAG (Retrieval Augmented Generation) 管理器
基于 ChromaDB 和 Google Gemini Embeddings 实现
"""

import os
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

class RAGManager:
    """
    RAG管理器
    
    功能:
    - 管理向量数据库 (ChromaDB)
    - 处理文本嵌入 (Gemini Embeddings)
    - 文档索引与检索
    """
    
    def __init__(self, persistence_dir: str):
        """
        初始化RAG管理器
        
        Args:
            persistence_dir: 向量数据库持久化目录
        """
        self.persistence_dir = Path(persistence_dir) / "chroma_db"
        self.persistence_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(path=str(self.persistence_dir))
        
        #获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name="novel_context",
            metadata={"hnsw:space": "cosine"}
        )
        
        # 确保API Key已配置 (假定GeminiClient已初始化，或环境变量存在)
        if not os.getenv("GEMINI_API_KEY"):
            logger.warning("GEMINI_API_KEY未设置，RAG功能可能不可用")
            
    def embed_text(self, text: str) -> List[float]:
        """
        使用Gemini生成嵌入向量
        """
        if not text.strip():
            return []
            
        try:
            # 使用 embedding-001 或 text-embedding-004
            model = "models/text-embedding-004"
            result = genai.embed_content(
                model=model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"生成嵌入失败: {e}")
            return []

    def add_documents(self, documents: List[str], metadatas: List[Dict], ids: List[str]):
        """
        添加文档到向量库
        """
        if not documents:
            return
            
        try:
            # 批量生成嵌入
            embeddings = []
            for doc in documents:
                emb = self.embed_text(doc)
                if emb:
                    embeddings.append(emb)
                else:
                    # 此时如果不匹配，会报错，简化处理: 填充0向量或跳过
                    # 这里为了健壮性，若失败则不添加该条
                    pass
            
            # 目前Gemini API限制，建议单条或小批量
            # 上面的循环已处理
            
            # 过滤掉空的embedding
            valid_docs = []
            valid_metas = []
            valid_ids = []
            valid_embs = []
            
            for i, emb in enumerate(embeddings):
                if emb:
                    valid_docs.append(documents[i])
                    valid_metas.append(metadatas[i])
                    valid_ids.append(ids[i])
                    valid_embs.append(emb)
            
            if valid_ids:
                self.collection.upsert(
                    documents=valid_docs,
                    embeddings=valid_embs,
                    metadatas=valid_metas,
                    ids=valid_ids
                )
                logger.info(f"成功索引 {len(valid_ids)} 条文档")
                
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise

    def query(self, query_text: str, n_results: int = 5, where: Optional[Dict] = None) -> List[str]:
        """
        检索相关文档
        """
        try:
            query_embedding = genai.embed_content(
                model="models/text-embedding-004",
                content=query_text,
                task_type="retrieval_query"
            )['embedding']
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            # 展平结果
            if results['documents']:
                return results['documents'][0]
            return []
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []
            
    def clear(self):
        """清空数据库"""
        self.client.delete_collection("novel_context")
        self.collection = self.client.get_or_create_collection("novel_context")
