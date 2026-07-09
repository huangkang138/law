"""
知识图谱相关路由
包括：节点管理、关系管理、图谱构建、查询等功能
"""

from flask import Blueprint, request, jsonify
from flask import make_response
from core.logger import app_logger
import uuid
import json
import sys
import os

# 确保系统编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 设置环境变量确保PostgreSQL使用UTF-8
os.environ['PGCLIENTENCODING'] = 'UTF8'

router = Blueprint('knowledge_graph', __name__)


def json_response(data, status_code=200):
    """
    返回支持中文的JSON响应
    """
    response = make_response(json.dumps(data, ensure_ascii=False))
    response.status_code = status_code
    response.content_type = 'application/json; charset=utf-8'
    return response


# ==================== 图谱管理接口 ====================

@router.route('/knowledge-graphs', methods=['GET'])
def get_graphs():
    """
    获取知识图谱列表
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeGraph, KnowledgeNode
        from sqlalchemy import func
        
        db = next(get_db())
        try:
            graphs = db.query(KnowledgeGraph).all()
            
            result = []
            for graph in graphs:
                # 统计节点数
                node_count = db.query(func.count(KnowledgeNode.id)).filter(KnowledgeNode.graph_id == graph.id).scalar()
                result.append({
                    "id": graph.id,
                    "name": graph.name,
                    "description": graph.description,
                    "node_count": node_count,
                    "created_at": graph.created_at.isoformat()
                })
            
            return json_response({
                "success": True,
                "graphs": result
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取知识图谱列表错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graph/upload', methods=['POST'])
def upload_file():
    """
    上传文件并分析构建知识图谱
    支持 PDF、Word、TXT 等文件格式
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeNode, KnowledgeRelationship, NodeType, RelationshipType
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # 获取图谱ID
        graph_id = request.args.get('graph_id', 'default')
        
        if 'file' not in request.files:
            return json_response({
                "success": False,
                "error": "没有上传文件"
            }, 400)
        
        file = request.files['file']
        if file.filename == '':
            return json_response({
                "success": False,
                "error": "没有选择文件"
            }, 400)
        
        # 读取文件内容
        filename = file.filename.lower()
        text_content = ""
        
        if filename.endswith('.txt'):
            try:
                text_content = file.read().decode('utf-8', errors='ignore')
            except Exception as e:
                app_logger.error(f"TXT文件解析错误: {str(e)}")
                return json_response({
                    "success": False,
                    "error": f"TXT文件解析错误: {str(e)}"
                }, 400)
        elif filename.endswith('.pdf'):
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            except ImportError:
                return json_response({
                    "success": False,
                    "error": "PDF解析库未安装"
                }, 500)
            except Exception as e:
                app_logger.error(f"PDF文件解析错误: {str(e)}")
                return json_response({
                    "success": False,
                    "error": f"PDF文件解析错误: {str(e)}"
                }, 400)
        elif filename.endswith('.docx'):
            try:
                from docx import Document
                doc = Document(file)
                for para in doc.paragraphs:
                    text_content += para.text + "\n"
            except ImportError:
                return json_response({
                    "success": False,
                    "error": "Word解析库未安装"
                }, 500)
            except Exception as e:
                app_logger.error(f"Word文件解析错误: {str(e)}")
                return json_response({
                    "success": False,
                    "error": f"Word文件解析错误: {str(e)}"
                }, 400)
        else:
            return json_response({
                "success": False,
                "error": "不支持的文件格式，请上传 PDF、Word 或 TXT 文件"
            }, 400)
        
        if not text_content.strip():
            return json_response({
                "success": False,
                "error": "文件内容为空"
            }, 400)
        
        app_logger.info(f"开始分析上传的文件: {file.filename}")
        
        # 使用LLM分析文本，提取实体和关系
        llm = LLMFactory.create_llm()
        
        prompt = f"""你是一名法律知识图谱专家，请分析以下法律文本，提取其中的实体和关系：

{text_content[:10000]}

请按照以下JSON格式输出：
{{
    "entities": [
        {{
            "name": "实体名称",
            "type": "实体类型（legal_article, case, legal_concept, legal_subject, legal_procedure, legal_profession, legal_institution, legal_event）",
            "description": "实体描述"
        }}
    ],
    "relationships": [
        {{
            "source": "源实体名称",
            "target": "目标实体名称",
            "type": "关系类型（cites, contains, involves, applies_to, belongs_to, performs, relates_to, derives_from, references）",
            "description": "关系描述"
        }}
    ]
}}

要求：
- 准确提取法律文本中的实体和关系
- 实体类型必须是指定的类型之一
- 关系类型必须是指定的类型之一
- 输出格式必须是有效的JSON"""
        
        messages = [
            SystemMessage(content="你是一名法律知识图谱专家，擅长从法律文本中提取实体和关系。"),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        result_content = response.content if hasattr(response, 'content') else str(response)
        
        try:
            if '```json' in result_content:
                json_str = result_content.split('```json')[1].split('```')[0].strip()
            elif '```' in result_content:
                json_str = result_content.split('```')[1].split('```')[0].strip()
            else:
                json_str = result_content.strip()
            
            graph_data = json.loads(json_str)
        except:
            return json_response({
                "success": False,
                "error": "LLM输出格式错误"
            }, 500)
        
        # 保存到数据库
        db = next(get_db())
        try:
            # 先保存实体
            entity_map = {}
            for entity in graph_data.get('entities', []):
                node = KnowledgeNode(
                    id=str(uuid.uuid4()),
                    graph_id=graph_id,
                    node_type=NodeType(entity.get('type', 'legal_concept')),
                    name=entity.get('name'),
                    content=entity.get('description', ''),
                    metadata_info=json.dumps({})
                )
                db.add(node)
                db.commit()
                db.refresh(node)
                entity_map[entity.get('name')] = node.id
            
            # 再保存关系
            for relationship in graph_data.get('relationships', []):
                source_name = relationship.get('source')
                target_name = relationship.get('target')
                
                if source_name in entity_map and target_name in entity_map:
                    rel = KnowledgeRelationship(
                        id=str(uuid.uuid4()),
                        graph_id=graph_id,
                        relationship_type=RelationshipType(relationship.get('type', 'relates_to')),
                        source_node_id=entity_map[source_name],
                        target_node_id=entity_map[target_name],
                        description=relationship.get('description', '')
                    )
                    db.add(rel)
            
            db.commit()
            
            app_logger.info(f"文件分析完成: {file.filename}")
            
            return json_response({
                "success": True,
                "message": "文件分析完成",
                "filename": file.filename,
                "entities_count": len(graph_data.get('entities', [])),
                "relationships_count": len(graph_data.get('relationships', []))
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"上传文件分析错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graphs', methods=['POST'])
def create_graph():
    """
    创建知识图谱
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeGraph
        
        data = request.json
        if not data or 'name' not in data:
            return json_response({
                "success": False,
                "error": "缺少必要参数 name"
            }, 400)
        
        name = data.get('name')
        description = data.get('description', '')
        
        db = next(get_db())
        try:
            graph = KnowledgeGraph(
                id=str(uuid.uuid4()),
                name=name,
                description=description
            )
            db.add(graph)
            db.commit()
            db.refresh(graph)
            
            app_logger.info(f"创建知识图谱成功: {graph.name}")
            
            return json_response({
                "success": True,
                "graph_id": str(graph.id),
                "graph": {
                    "id": str(graph.id),
                    "name": graph.name,
                    "description": graph.description,
                    "created_at": graph.created_at.isoformat() if graph.created_at else None
                }
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"创建知识图谱错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graphs/<graph_id>', methods=['PUT'])
def update_graph(graph_id):
    """
    更新知识图谱
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeGraph
        
        data = request.json
        if not data:
            return json_response({
                "success": False,
                "error": "缺少请求数据"
            }, 400)
        
        db = next(get_db())
        try:
            # 检查图谱是否存在
            graph = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == graph_id).first()
            if not graph:
                return json_response({
                    "success": False,
                    "error": "图谱不存在"
                }, 404)
            
            # 更新图谱信息
            if 'name' in data:
                graph.name = data['name']
            if 'description' in data:
                graph.description = data['description']
            
            db.commit()
            db.refresh(graph)
            
            app_logger.info(f"更新知识图谱成功: {graph_id}")
            
            return json_response({
                "success": True,
                "message": "更新成功",
                "graph": {
                    "id": str(graph.id),
                    "name": graph.name,
                    "description": graph.description,
                    "created_at": graph.created_at.isoformat() if graph.created_at else None
                }
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"更新知识图谱错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graphs/<graph_id>', methods=['DELETE'])
def delete_graph(graph_id):
    """
    删除知识图谱
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeGraph, KnowledgeNode, KnowledgeRelationship
        
        db = next(get_db())
        try:
            # 检查图谱是否存在
            graph = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == graph_id).first()
            if not graph:
                return json_response({
                    "success": False,
                    "error": "图谱不存在"
                }, 404)
            
            # 先删除所有关联的关系
            db.query(KnowledgeRelationship).filter(KnowledgeRelationship.graph_id == graph_id).delete(synchronize_session=False)
            
            # 再删除所有关联的节点
            db.query(KnowledgeNode).filter(KnowledgeNode.graph_id == graph_id).delete(synchronize_session=False)
            
            # 最后删除图谱
            db.delete(graph)
            db.commit()
            
            app_logger.info(f"删除知识图谱成功: {graph_id}")
            
            return json_response({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除知识图谱错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graphs/batch-delete', methods=['POST'])
def batch_delete_graphs():
    """
    批量删除知识图谱
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeGraph, KnowledgeNode, KnowledgeRelationship
        
        data = request.json
        if not data or 'graph_ids' not in data:
            return json_response({
                "success": False,
                "error": "缺少必要参数 graph_ids"
            }, 400)
        
        graph_ids = data.get('graph_ids', [])
        if not graph_ids:
            return json_response({
                "success": False,
                "error": "graph_ids 不能为空"
            }, 400)
        
        db = next(get_db())
        try:
            deleted_count = 0
            failed_ids = []
            
            for graph_id in graph_ids:
                # 检查图谱是否存在
                graph = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == graph_id).first()
                if not graph:
                    failed_ids.append(graph_id)
                    continue
                
                # 先删除所有关联的关系
                db.query(KnowledgeRelationship).filter(KnowledgeRelationship.graph_id == graph_id).delete(synchronize_session=False)
                
                # 再删除所有关联的节点
                db.query(KnowledgeNode).filter(KnowledgeNode.graph_id == graph_id).delete(synchronize_session=False)
                
                # 最后删除图谱
                db.delete(graph)
                deleted_count += 1
            
            db.commit()
            
            app_logger.info(f"批量删除知识图谱成功: {deleted_count} 个")
            
            return json_response({
                "success": True,
                "message": f"成功删除 {deleted_count} 个图谱",
                "deleted_count": deleted_count,
                "failed_ids": failed_ids
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"批量删除知识图谱错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


# ==================== 节点管理接口 ====================

@router.route('/knowledge-graph/nodes', methods=['POST'])
def create_node():
    """
    创建知识节点
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeNode, NodeType
        
        data = request.json
        if not data or 'node_type' not in data or 'name' not in data:
            return json_response({
                "success": False,
                "error": "缺少必要参数 node_type 和 name"
            }, 400)
        
        # 获取图谱ID
        graph_id = request.args.get('graph_id', 'default')
        
        node_type = data.get('node_type')
        name = data.get('name')
        content = data.get('content', '')
        metadata_info = data.get('metadata_info', {})
        
        # 验证节点类型
        if node_type not in [nt.value for nt in NodeType]:
            return json_response({
                "success": False,
                "error": f"无效的节点类型，支持的类型：{[nt.value for nt in NodeType]}"
            }, 400)
        
        db = next(get_db())
        try:
            app_logger.info(f"准备创建节点 - 名称: {name}, 内容: {content}")
            node = KnowledgeNode(
                id=str(uuid.uuid4()),
                graph_id=graph_id,
                node_type=NodeType(node_type),
                name=name,
                content=content,
                metadata_info=json.dumps(metadata_info) if isinstance(metadata_info, dict) else metadata_info
            )
            db.add(node)
            db.commit()
            db.refresh(node)
            
            app_logger.info(f"创建知识节点成功: {node.name}")
            
            # 创建响应，确保使用UTF-8编码
            response_data = {
                "success": True,
                "node_id": node.id,
                "node": {
                    "id": node.id,
                    "node_type": node.node_type.value,
                    "name": node.name,
                    "content": node.content,
                    "metadata_info": json.loads(node.metadata_info) if node.metadata_info else {},
                    "created_at": node.created_at.isoformat()
                }
            }
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"创建知识节点错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graph/nodes', methods=['GET'])
def get_nodes():
    """
    获取节点列表
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeNode
        
        # 获取图谱ID
        graph_id = request.args.get('graph_id', 'default')
        
        db = next(get_db())
        try:
            nodes = db.query(KnowledgeNode).filter(KnowledgeNode.graph_id == graph_id).all()
            
            result = []
            for node in nodes:
                result.append({
                    "id": node.id,
                    "node_type": node.node_type.value,
                    "name": node.name,
                    "content": node.content,
                    "metadata_info": json.loads(node.metadata_info) if node.metadata_info else {},
                    "created_at": node.created_at.isoformat()
                })
            
            return json_response({
                "success": True,
                "nodes": result
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取知识节点列表错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graph/nodes/<node_id>', methods=['GET'])
def get_node(node_id):
    """
    获取单个知识节点
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeNode
        
        db = next(get_db())
        try:
            node = db.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()
            if not node:
                return json_response({
                    "success": False,
                    "error": "节点不存在"
                }, 404)
            
            return json_response({
                "success": True,
                "node": {
                    "id": str(node.id),
                    "node_type": node.node_type.value,
                    "name": node.name,
                    "content": node.content,
                    "metadata_info": json.loads(node.metadata_info) if node.metadata_info else {},
                    "created_at": node.created_at.isoformat() if node.created_at else None
                }
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取知识节点错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graph/nodes/<node_id>', methods=['PUT'])
def update_node(node_id):
    """
    更新知识节点
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeNode, NodeType
        
        data = request.json
        
        db = next(get_db())
        try:
            node = db.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()
            if not node:
                return json_response({
                    "success": False,
                    "error": "节点不存在"
                }, 404)
            
            # 更新节点属性
            if 'name' in data:
                node.name = data['name']
            if 'content' in data:
                node.content = data['content']
            if 'metadata_info' in data:
                node.metadata_info = json.dumps(data['metadata_info']) if isinstance(data['metadata_info'], dict) else data['metadata_info']
            if 'node_type' in data:
                if data['node_type'] not in [nt.value for nt in NodeType]:
                    return json_response({
                        "success": False,
                        "error": f"无效的节点类型，支持的类型：{[nt.value for nt in NodeType]}"
                    }, 400)
                node.node_type = NodeType(data['node_type'])
            
            db.commit()
            db.refresh(node)
            
            app_logger.info(f"更新知识节点成功: {node.name}")
            
            return json_response({
                "success": True,
                "node": {
                    "id": str(node.id),
                    "node_type": node.node_type.value,
                    "name": node.name,
                    "content": node.content,
                    "metadata_info": json.loads(node.metadata_info) if node.metadata_info else {},
                    "created_at": node.created_at.isoformat() if node.created_at else None
                }
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"更新知识节点错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graph/nodes/<node_id>', methods=['DELETE'])
def delete_node(node_id):
    """
    删除知识节点
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeNode, KnowledgeRelationship
        
        # 获取图谱ID
        graph_id = request.args.get('graph_id', 'default')
        
        db = next(get_db())
        try:
            # 检查节点是否存在
            node = db.query(KnowledgeNode).filter(
                KnowledgeNode.id == node_id,
                KnowledgeNode.graph_id == graph_id
            ).first()
            
            if not node:
                return json_response({
                    "success": False,
                    "error": "节点不存在"
                }, 404)
            
            # 先删除所有关联的关系，避免外键约束错误
            db.query(KnowledgeRelationship).filter(
                KnowledgeRelationship.graph_id == graph_id,
                ((KnowledgeRelationship.source_node_id == node_id) |
                (KnowledgeRelationship.target_node_id == node_id))
            ).delete(synchronize_session=False)
            
            # 再删除节点
            db.delete(node)
            db.commit()
            
            app_logger.info(f"删除知识节点成功: {node_id}")
            
            return json_response({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除知识节点错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


# ==================== 关系管理接口 ====================

@router.route('/knowledge-graph/relationships', methods=['POST'])
def create_relationship():
    """
    创建知识关系
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeRelationship, RelationshipType, KnowledgeNode
        
        data = request.json
        if not data or 'source_node_id' not in data or 'target_node_id' not in data or 'relationship_type' not in data:
            return json_response({
                "success": False,
                "error": "缺少必要参数 source_node_id, target_node_id 和 relationship_type"
            }, 400)
        
        # 获取图谱ID
        graph_id = request.args.get('graph_id', 'default')
        
        source_node_id = data.get('source_node_id')
        target_node_id = data.get('target_node_id')
        relationship_type = data.get('relationship_type')
        weight = data.get('weight')
        description = data.get('description')
        
        # 验证关系类型
        if relationship_type not in [rt.value for rt in RelationshipType]:
            return json_response({
                "success": False,
                "error": f"无效的关系类型，支持的类型：{[rt.value for rt in RelationshipType]}"
            }, 400)
        
        db = next(get_db())
        try:
            # 验证节点是否存在
            source_node = db.query(KnowledgeNode).filter(
                KnowledgeNode.id == source_node_id,
                KnowledgeNode.graph_id == graph_id
            ).first()
            target_node = db.query(KnowledgeNode).filter(
                KnowledgeNode.id == target_node_id,
                KnowledgeNode.graph_id == graph_id
            ).first()
            
            if not source_node:
                return json_response({
                    "success": False,
                    "error": "源节点不存在"
                }, 404)
            
            if not target_node:
                return json_response({
                    "success": False,
                    "error": "目标节点不存在"
                }, 404)
            
            relationship = KnowledgeRelationship(
                id=str(uuid.uuid4()),
                graph_id=graph_id,
                relationship_type=RelationshipType(relationship_type),
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                weight=weight,
                description=description
            )
            db.add(relationship)
            db.commit()
            db.refresh(relationship)
            
            app_logger.info(f"创建知识关系成功: {source_node.name} -> {target_node.name}")
            
            return json_response({
                "success": True,
                "relationship_id": str(relationship.id),
                "relationship": {
                    "id": str(relationship.id),
                    "relationship_type": relationship.relationship_type.value,
                    "source_node_id": str(relationship.source_node_id),
                    "target_node_id": str(relationship.target_node_id),
                    "weight": relationship.weight,
                    "description": relationship.description,
                    "created_at": relationship.created_at.isoformat() if relationship.created_at else None
                }
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"创建知识关系错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graph/relationships', methods=['GET'])
def get_relationships():
    """
    获取知识关系列表
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeRelationship
        
        # 获取图谱ID
        graph_id = request.args.get('graph_id', 'default')
        
        db = next(get_db())
        try:
            relationships = db.query(KnowledgeRelationship).filter(KnowledgeRelationship.graph_id == graph_id).all()
            
            result = []
            for relationship in relationships:
                result.append({
                    "id": relationship.id,
                    "relationship_type": relationship.relationship_type.value,
                    "source_node_id": relationship.source_node_id,
                    "target_node_id": relationship.target_node_id,
                    "weight": relationship.weight,
                    "description": relationship.description,
                    "created_at": relationship.created_at.isoformat()
                })
            
            return json_response({
                "success": True,
                "relationships": result
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取知识关系列表错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graph/relationships/<relationship_id>', methods=['DELETE'])
def delete_relationship(relationship_id):
    """
    删除知识关系
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeRelationship
        
        db = next(get_db())
        try:
            relationship = db.query(KnowledgeRelationship).filter(KnowledgeRelationship.id == relationship_id).first()
            if not relationship:
                return json_response({
                    "success": False,
                    "error": "关系不存在"
                }, 404)
            
            db.delete(relationship)
            db.commit()
            
            app_logger.info(f"删除知识关系成功: {relationship.id}")
            
            return json_response({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除知识关系错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


# ==================== 图谱构建和查询接口 ====================

@router.route('/knowledge-graph/structure', methods=['GET'])
def get_graph_structure():
    """
    获取知识图谱结构
    返回节点和关系的完整结构，用于前端可视化
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeNode, KnowledgeRelationship
        
        # 获取图谱ID
        graph_id = request.args.get('graph_id', 'default')
        
        db = next(get_db())
        try:
            # 获取所有节点
            nodes = db.query(KnowledgeNode).filter(KnowledgeNode.graph_id == graph_id).all()
            # 获取所有关系
            relationships = db.query(KnowledgeRelationship).filter(KnowledgeRelationship.graph_id == graph_id).all()
            
            # 构建节点列表
            nodes_list = []
            for node in nodes:
                nodes_list.append({
                    "id": node.id,
                    "label": node.name,
                    "type": node.node_type.value,
                    "properties": {
                        "content": node.content,
                        "metadata": json.loads(node.metadata_info) if node.metadata_info else {}
                    }
                })
            
            # 构建关系列表
            relationships_list = []
            for relationship in relationships:
                relationships_list.append({
                    "id": relationship.id,
                    "source": relationship.source_node_id,
                    "target": relationship.target_node_id,
                    "label": relationship.relationship_type.value,
                    "properties": {
                        "weight": relationship.weight,
                        "description": relationship.description
                    }
                })
            
            return json_response({
                "success": True,
                "nodes": nodes_list,
                "relationships": relationships_list
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取知识图谱结构错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graph/search', methods=['GET'])
def search_nodes():
    """
    搜索知识节点
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeNode
        
        # 获取图谱ID
        graph_id = request.args.get('graph_id', 'default')
        
        query = request.args.get('q', '')
        if not query:
            return json_response({
                "success": False,
                "error": "缺少搜索关键词"
            }, 400)
        
        db = next(get_db())
        try:
            # 搜索节点名称和内容
            nodes = db.query(KnowledgeNode).filter(
                KnowledgeNode.graph_id == graph_id,
                (KnowledgeNode.name.ilike(f'%{query}%') | 
                KnowledgeNode.content.ilike(f'%{query}%'))
            ).all()
            
            result = []
            for node in nodes:
                result.append({
                    "id": node.id,
                    "node_type": node.node_type.value,
                    "name": node.name,
                    "content": node.content,
                    "metadata_info": json.loads(node.metadata_info) if node.metadata_info else {},
                    "created_at": node.created_at.isoformat()
                })
            
            return json_response({
                "success": True,
                "nodes": result
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"搜索知识节点错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)


@router.route('/knowledge-graph/build', methods=['POST'])
def build_graph():
    """
    构建知识图谱
    根据输入的法律文本自动构建知识图谱
    """
    try:
        from core.database import get_db
        from models.knowledge_graph import KnowledgeNode, KnowledgeRelationship, NodeType, RelationshipType
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        
        data = request.json
        if not data or 'text' not in data:
            return json_response({
                "success": False,
                "error": "缺少必要参数 text"
            }, 400)
        
        # 获取图谱ID
        graph_id = request.args.get('graph_id', 'default')
        
        text = data.get('text')
        
        app_logger.info("开始构建知识图谱...")
        
        # 使用LLM分析文本，提取实体和关系
        llm = LLMFactory.create_llm()
        
        prompt = f"""你是一名法律知识图谱专家，请分析以下法律文本，提取其中的实体和关系：

{text}

请按照以下JSON格式输出：
{{
    "entities": [
        {{
            "name": "实体名称",
            "type": "实体类型（legal_article, case, legal_concept, legal_subject, legal_procedure, legal_profession, legal_institution, legal_event）",
            "description": "实体描述"
        }}
    ],
    "relationships": [
        {{
            "source": "源实体名称",
            "target": "目标实体名称",
            "type": "关系类型（cites, contains, involves, applies_to, belongs_to, performs, relates_to, derives_from, references）",
            "description": "关系描述"
        }}
    ]
}}

要求：
- 准确提取法律文本中的实体和关系
- 实体类型必须是指定的类型之一
- 关系类型必须是指定的类型之一
- 输出格式必须是有效的JSON"""
        
        messages = [
            SystemMessage(content="你是一名法律知识图谱专家，擅长从法律文本中提取实体和关系。"),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        result_content = response.content if hasattr(response, 'content') else str(response)
        
        try:
            if '```json' in result_content:
                json_str = result_content.split('```json')[1].split('```')[0].strip()
            elif '```' in result_content:
                json_str = result_content.split('```')[1].split('```')[0].strip()
            else:
                json_str = result_content.strip()
            
            graph_data = json.loads(json_str)
        except:
            return json_response({
                "success": False,
                "error": "LLM输出格式错误"
            }, 500)
        
        # 保存到数据库
        db = next(get_db())
        try:
            # 先保存实体
            entity_map = {}
            for entity in graph_data.get('entities', []):
                node = KnowledgeNode(
                    id=str(uuid.uuid4()),
                    graph_id=graph_id,
                    node_type=NodeType(entity.get('type', 'legal_concept')),
                    name=entity.get('name'),
                    content=entity.get('description', ''),
                    metadata_info=json.dumps({})
                )
                db.add(node)
                db.commit()
                db.refresh(node)
                entity_map[entity.get('name')] = node.id
            
            # 再保存关系
            for relationship in graph_data.get('relationships', []):
                source_name = relationship.get('source')
                target_name = relationship.get('target')
                
                if source_name in entity_map and target_name in entity_map:
                    rel = KnowledgeRelationship(
                        id=str(uuid.uuid4()),
                        graph_id=graph_id,
                        relationship_type=RelationshipType(relationship.get('type', 'relates_to')),
                        source_node_id=entity_map[source_name],
                        target_node_id=entity_map[target_name],
                        description=relationship.get('description', '')
                    )
                    db.add(rel)
            
            db.commit()
            
            app_logger.info("知识图谱构建成功")
            
            return json_response({
                "success": True,
                "message": "知识图谱构建成功",
                "entities_count": len(graph_data.get('entities', [])),
                "relationships_count": len(graph_data.get('relationships', []))
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"构建知识图谱错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return json_response({
            "success": False,
            "error": str(e)
        }, 500)
