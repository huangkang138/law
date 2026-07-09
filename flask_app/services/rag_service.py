"""
RAG 服务
"""

import uuid
from flask_app.core.logger import app_logger
from flask_app.services.legal_chunker import LegalChunker


class RAGService:
    """
    RAG 服务
    """
    
    def __init__(self):
        """
        初始化 RAG 服务
        """
        self.chunker = LegalChunker()
        self.contracts = {}
        app_logger.info("✅ RAG 服务初始化完成")
    
    def ingest_contract(self, text: str, contract_id: str = None, metadata: dict = None) -> dict:
        """
        入库合同
        
        Args:
            text: 合同文本
            contract_id: 合同 ID
            metadata: 元数据
            
        Returns:
            入库结果
        """
        try:
            # 生成合同 ID
            if not contract_id:
                contract_id = f"contract_{uuid.uuid4()}"
            
            # 分块
            chunks = self.chunker.chunk_text(text)
            
            # 模拟入库（实际项目中应存入向量数据库）
            self.contracts[contract_id] = {
                "text": text,
                "chunks": chunks,
                "metadata": metadata or {},
                "chunk_count": len(chunks)
            }
            
            app_logger.info(f"合同入库成功: {contract_id}, 切片数: {len(chunks)}")
            
            return {
                "contract_id": contract_id,
                "chunk_count": len(chunks)
            }
            
        except Exception as e:
            app_logger.error(f"合同入库错误: {str(e)}")
            raise
    
    def retrieve(self, query: str, contract_id: str = None, top_k: int = 3) -> list:
        """
        检索相关内容
        
        Args:
            query: 查询文本
            contract_id: 合同 ID
            top_k: 返回结果数量
            
        Returns:
            检索结果
        """
        try:
            # 模拟检索（实际项目中应使用向量相似度搜索）
            results = []
            
            if contract_id and contract_id in self.contracts:
                # 针对特定合同检索
                contract = self.contracts[contract_id]
                for i, chunk in enumerate(contract["chunks"]):
                    results.append({
                        "chunk_id": f"{contract_id}_chunk_{i}",
                        "content": chunk,
                        "score": 0.8
                    })
            else:
                # 全局检索
                for cid, contract in self.contracts.items():
                    for i, chunk in enumerate(contract["chunks"]):
                        results.append({
                            "contract_id": cid,
                            "chunk_id": f"{cid}_chunk_{i}",
                            "content": chunk,
                            "score": 0.7
                        })
            
            # 排序并返回前 top_k 个结果
            results.sort(key=lambda x: x["score"], reverse=True)
            
            app_logger.info(f"检索完成，找到 {len(results)} 个结果")
            return results[:top_k]
            
        except Exception as e:
            app_logger.error(f"检索错误: {str(e)}")
            raise


# 单例实例
_rag_service = None


def get_rag_service() -> RAGService:
    """
    获取 RAG 服务实例
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
