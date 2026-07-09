"""
法律知识图谱数据库模型

定义知识图谱的节点和关系模型
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from core.database import Base


class NodeType(enum.Enum):
    """节点类型枚举"""
    LEGAL_ARTICLE = "legal_article"  # 法律条款
    CASE = "case"  # 案例
    LEGAL_CONCEPT = "legal_concept"  # 法律概念
    LEGAL_SUBJECT = "legal_subject"  # 法律主体
    LEGAL_PROCEDURE = "legal_procedure"  # 法律程序
    LEGAL_PROFESSION = "legal_profession"  # 法律职业
    LEGAL_INSTITUTION = "legal_institution"  # 法律机构
    LEGAL_EVENT = "legal_event"  # 法律事件


class RelationshipType(enum.Enum):
    """关系类型枚举"""
    CITES = "cites"  # 引用
    CONTAINS = "contains"  # 包含
    INVOLVES = "involves"  # 涉及
    APPLIES_TO = "applies_to"  # 适用
    BELONGS_TO = "belongs_to"  # 属于
    PERFORMS = "performs"  # 执行
    RELATES_TO = "relates_to"  # 相关
    DERIVES_FROM = "derives_from"  # 源自
    REFERENCES = "references"  # 参考


class KnowledgeGraph(Base):
    """知识图谱模型"""
    __tablename__ = "knowledge_graphs"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class KnowledgeNode(Base):
    """知识节点模型"""
    __tablename__ = "knowledge_nodes"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID
    graph_id = Column(String(36), nullable=False, index=True)  # 图谱ID
    node_type = Column(SQLEnum(NodeType), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=True)  # 节点内容
    metadata_info = Column(Text, nullable=True)  # 元数据，JSON格式
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    outgoing_relationships = relationship("KnowledgeRelationship", foreign_keys="KnowledgeRelationship.source_node_id", back_populates="source_node")
    incoming_relationships = relationship("KnowledgeRelationship", foreign_keys="KnowledgeRelationship.target_node_id", back_populates="target_node")


class KnowledgeRelationship(Base):
    """知识关系模型"""
    __tablename__ = "knowledge_relationships"
    
    id = Column(String(36), primary_key=True, index=True)  # UUID
    graph_id = Column(String(36), nullable=False, index=True)  # 图谱ID
    relationship_type = Column(SQLEnum(RelationshipType), nullable=False, index=True)
    source_node_id = Column(String(36), ForeignKey("knowledge_nodes.id"), nullable=False, index=True)
    target_node_id = Column(String(36), ForeignKey("knowledge_nodes.id"), nullable=False, index=True)
    weight = Column(String(100), nullable=True)  # 关系权重或强度
    description = Column(Text, nullable=True)  # 关系描述
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    source_node = relationship("KnowledgeNode", foreign_keys=[source_node_id], back_populates="outgoing_relationships")
    target_node = relationship("KnowledgeNode", foreign_keys=[target_node_id], back_populates="incoming_relationships")
