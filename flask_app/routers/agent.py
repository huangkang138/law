"""
智能体管理路由
"""

import uuid
import time
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from core.database import get_db
from models.db_models import Agent, AgentUsage
from services.llm_factory import LLMFactory
from core.logger import app_logger
from langchain_core.messages import HumanMessage, SystemMessage


agent_bp = Blueprint('agent', __name__, url_prefix='/api/agents')


def _invoke_llm_streaming(messages: list, custom_config: dict = None) -> str:
    """
    使用流式传输调用LLM
    
    Args:
        messages: 消息列表
        custom_config: 自定义LLM配置
        
    Returns:
        str: LLM响应内容
    """
    import httpx
    import json
    from core.config import settings
    
    # 获取LLM配置
    if custom_config:
        api_key = custom_config.get("api_key", settings.OPENAI_API_KEY)
        base_url = custom_config.get("base_url", settings.OPENAI_BASE_URL)
        model = custom_config.get("model", settings.OPENAI_MODEL)
    else:
        api_key = settings.OPENAI_API_KEY
        base_url = settings.OPENAI_BASE_URL
        model = settings.OPENAI_MODEL
    
    # 转换消息格式
    formatted_messages = []
    for msg in messages:
        if hasattr(msg, '_type'):
            if msg._type == 'system':
                formatted_messages.append({"role": "system", "content": msg.content})
            elif msg._type == 'human':
                formatted_messages.append({"role": "user", "content": msg.content})
            elif msg._type == 'ai':
                formatted_messages.append({"role": "assistant", "content": msg.content})
        elif hasattr(msg, 'type'):
            if msg.type == 'system':
                formatted_messages.append({"role": "system", "content": msg.content})
            elif msg.type == 'human':
                formatted_messages.append({"role": "user", "content": msg.content})
    
    # 构建请求数据
    payload = {
        "model": model,
        "messages": formatted_messages,
        "temperature": custom_config.get("temperature", settings.OPENAI_TEMPERATURE) if custom_config else settings.OPENAI_TEMPERATURE,
        "max_tokens": custom_config.get("max_tokens", settings.OPENAI_MAX_TOKENS) if custom_config else settings.OPENAI_MAX_TOKENS,
        "stream": True
    }
    
    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 使用流式传输发送请求
    client = httpx.Client(timeout=180.0)
    content = ""
    
    try:
        with client.stream(
            "POST",
            f"{base_url}/chat/completions",
            json=payload,
            headers=headers
        ) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line = line.strip()
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    chunk_content = delta.get('content', '')
                                    if chunk_content:
                                        content += chunk_content
                            except json.JSONDecodeError:
                                continue
                return content
            else:
                error_text = ""
                try:
                    for line in response.iter_lines():
                        if line:
                            error_text += line
                except:
                    pass
                raise Exception(f"LLM调用失败: {response.status_code}")
    finally:
        client.close()
    
    return content


@agent_bp.route('/', methods=['GET'])
def get_agents():
    """
    获取智能体列表
    
    Query参数：
    - user_id: 用户ID（可选）
    - agent_type: 智能体类型（可选）
    - is_preset: 是否为预设智能体（可选）
    - is_active: 是否启用（可选）
    """
    try:
        db: Session = next(get_db())
        
        # 构建查询
        query = db.query(Agent)
        
        # 过滤条件
        user_id = request.args.get('user_id', 'anonymous')
        agent_type = request.args.get('agent_type')
        is_preset = request.args.get('is_preset')
        is_active = request.args.get('is_active')
        
        query = query.filter(Agent.user_id == user_id)
        
        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        if is_preset is not None:
            query = query.filter(Agent.is_preset == (is_preset.lower() == 'true'))
        if is_active is not None:
            query = query.filter(Agent.is_active == (is_active.lower() == 'true'))
        
        # 排序：预设智能体优先，然后按使用次数降序，最后按更新时间降序
        agents = query.order_by(Agent.is_preset.desc(), Agent.usage_count.desc(), Agent.updated_at.desc()).all()
        
        result = []
        for agent in agents:
            result.append({
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "avatar": agent.avatar,
                "agent_type": agent.agent_type,
                "temperature": agent.temperature,
                "max_tokens": agent.max_tokens,
                "top_p": agent.top_p,
                "is_preset": agent.is_preset,
                "is_active": agent.is_active,
                "usage_count": agent.usage_count,
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
            })
        
        db.close()
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        app_logger.error(f"获取智能体列表失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agent_bp.route('/<agent_id>', methods=['GET'])
def get_agent(agent_id: str):
    """
    获取单个智能体详情
    
    Args:
        agent_id: 智能体ID
    """
    try:
        db: Session = next(get_db())
        
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            db.close()
            return jsonify({
                "success": False,
                "error": "智能体不存在"
            }), 404
        
        result = {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "avatar": agent.avatar,
            "system_prompt": agent.system_prompt,
            "agent_type": agent.agent_type,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "top_p": agent.top_p,
            "is_preset": agent.is_preset,
            "is_active": agent.is_active,
            "user_id": agent.user_id,
            "usage_count": agent.usage_count,
            "config": agent.config,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
        }
        
        db.close()
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        app_logger.error(f"获取智能体详情失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agent_bp.route('/', methods=['POST'])
def create_agent():
    """
    创建智能体
    
    Body参数：
    - name: 智能体名称（必填）
    - description: 智能体描述
    - avatar: 智能体头像URL
    - system_prompt: 系统提示词（必填）
    - agent_type: 智能体类型（必填）
    - temperature: 温度参数（0-100）
    - max_tokens: 最大token数
    - top_p: top_p参数（0-100）
    - is_active: 是否启用
    - config: 额外配置参数
    """
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('name') or not data.get('system_prompt') or not data.get('agent_type'):
            return jsonify({
                "success": False,
                "error": "缺少必填字段：name, system_prompt, agent_type"
            }), 400
        
        db: Session = next(get_db())
        
        # 创建智能体
        agent = Agent(
            id=str(uuid.uuid4()),
            name=data.get('name'),
            description=data.get('description'),
            avatar=data.get('avatar'),
            system_prompt=data.get('system_prompt'),
            agent_type=data.get('agent_type'),
            temperature=data.get('temperature', 70),
            max_tokens=data.get('max_tokens', 2000),
            top_p=data.get('top_p', 90),
            is_preset=False,  # 用户创建的不是预设智能体
            is_active=data.get('is_active', True),
            user_id=data.get('user_id', 'anonymous'),
            usage_count=0,
            config=data.get('config', {})
        )
        
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        result = {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "avatar": agent.avatar,
            "agent_type": agent.agent_type,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "top_p": agent.top_p,
            "is_preset": agent.is_preset,
            "is_active": agent.is_active,
            "usage_count": agent.usage_count,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
        }
        
        db.close()
        
        app_logger.info(f"创建智能体成功: {agent.name} ({agent.id})")
        
        return jsonify({
            "success": True,
            "data": result
        }), 201
    
    except Exception as e:
        app_logger.error(f"创建智能体失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agent_bp.route('/<agent_id>', methods=['PUT'])
def update_agent(agent_id: str):
    """
    更新智能体
    
    Args:
        agent_id: 智能体ID
    
    Body参数：
    - name: 智能体名称
    - description: 智能体描述
    - avatar: 智能体头像URL
    - system_prompt: 系统提示词
    - agent_type: 智能体类型
    - temperature: 温度参数（0-100）
    - max_tokens: 最大token数
    - top_p: top_p参数（0-100）
    - is_active: 是否启用
    - config: 额外配置参数
    """
    try:
        data = request.get_json()
        
        db: Session = next(get_db())
        
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            db.close()
            return jsonify({
                "success": False,
                "error": "智能体不存在"
            }), 404
        
        # 预设智能体不允许修改系统提示词
        if agent.is_preset and 'system_prompt' in data:
            return jsonify({
                "success": False,
                "error": "预设智能体不允许修改系统提示词"
            }), 400
        
        # 更新字段
        if 'name' in data:
            agent.name = data['name']
        if 'description' in data:
            agent.description = data['description']
        if 'avatar' in data:
            agent.avatar = data['avatar']
        if 'system_prompt' in data:
            agent.system_prompt = data['system_prompt']
        if 'agent_type' in data:
            agent.agent_type = data['agent_type']
        if 'temperature' in data:
            agent.temperature = data['temperature']
        if 'max_tokens' in data:
            agent.max_tokens = data['max_tokens']
        if 'top_p' in data:
            agent.top_p = data['top_p']
        if 'is_active' in data:
            agent.is_active = data['is_active']
        if 'config' in data:
            agent.config = data['config']
        
        db.commit()
        db.refresh(agent)
        
        result = {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "avatar": agent.avatar,
            "agent_type": agent.agent_type,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "top_p": agent.top_p,
            "is_preset": agent.is_preset,
            "is_active": agent.is_active,
            "usage_count": agent.usage_count,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
        }
        
        db.close()
        
        app_logger.info(f"更新智能体成功: {agent.name} ({agent.id})")
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        app_logger.error(f"更新智能体失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agent_bp.route('/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id: str):
    """
    删除智能体
    
    Args:
        agent_id: 智能体ID
    """
    try:
        db: Session = next(get_db())
        
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            db.close()
            return jsonify({
                "success": False,
                "error": "智能体不存在"
            }), 404
        
        # 预设智能体不允许删除
        if agent.is_preset:
            db.close()
            return jsonify({
                "success": False,
                "error": "预设智能体不允许删除"
            }), 400
        
        # 删除智能体的使用记录
        db.query(AgentUsage).filter(AgentUsage.agent_id == agent_id).delete()
        
        # 删除智能体
        db.delete(agent)
        db.commit()
        
        db.close()
        
        app_logger.info(f"删除智能体成功: {agent.name} ({agent_id})")
        
        return jsonify({
            "success": True,
            "message": "智能体删除成功"
        })
    
    except Exception as e:
        app_logger.error(f"删除智能体失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def _clean_response_text(text: str) -> str:
    """
    清理智能体回复文本，移除不需要的特殊字符
    
    Args:
        text: 原始文本
    
    Returns:
        清理后的文本
    """
    import re
    
    # 移除Markdown格式的粗体、斜体、标题等标记
    # 移除 **粗体**
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # 移除 *斜体*
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    # 移除 # 标题标记
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # 移除 - 列表标记
    text = re.sub(r'^-\s+', '', text, flags=re.MULTILINE)
    # 移除 ## 标题标记
    text = re.sub(r'##+', '', text)
    # 移除连续的星号
    text = re.sub(r'\*{3,}', '', text)
    # 移除连续的井号
    text = re.sub(r'#{3,}', '', text)
    # 移除连续的横线
    text = re.sub(r'-{3,}', '', text)
    
    # 清理多余的空行
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()


@agent_bp.route('/<agent_id>/chat', methods=['POST'])
def chat_with_agent(agent_id: str):
    """
    使用智能体进行对话
    
    Args:
        agent_id: 智能体ID
    
    Body参数：
    - message: 用户消息（必填）
    - session_id: 会话ID（可选）
    - custom_config: 自定义LLM配置（可选）
    """
    try:
        data = request.get_json()
        
        if not data.get('message'):
            return jsonify({
                "success": False,
                "error": "缺少必填字段：message"
            }), 400
        
        message = data.get('message')
        session_id = data.get('session_id', str(uuid.uuid4()))
        custom_config = data.get('custom_config')
        
        db: Session = next(get_db())
        
        # 获取智能体
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            db.close()
            return jsonify({
                "success": False,
                "error": "智能体不存在"
            }), 404
        
        if not agent.is_active:
            db.close()
            return jsonify({
                "success": False,
                "error": "智能体未启用"
            }), 400
        
        # 获取智能体信息（在关闭会话之前）
        agent_name = agent.name
        agent_user_id = agent.user_id
        system_prompt = agent.system_prompt
        temperature = agent.temperature
        max_tokens = agent.max_tokens
        top_p = agent.top_p
        
        # 关闭数据库会话
        db.close()
        
        # 记录开始时间
        start_time = time.time()
        
        # 构建消息
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]
        
        # 构建自定义配置
        agent_config = {
            "temperature": temperature / 100.0,
            "max_tokens": max_tokens,
            "top_p": top_p / 100.0
        }
        
        if custom_config:
            agent_config.update(custom_config)
        
        # 调用LLM
        response = _invoke_llm_streaming(messages, agent_config)
        
        # 计算响应时间
        response_time = int((time.time() - start_time) * 1000)
        
        # 清理响应文本
        cleaned_response = _clean_response_text(response)
        
        # 重新打开数据库会话进行更新
        db: Session = next(get_db())
        
        try:
            # 更新智能体使用次数
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                agent.usage_count += 1
                db.commit()
            
            # 记录使用（保存清理后的响应）
            usage = AgentUsage(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                user_id=agent_user_id,
                session_id=session_id,
                user_input=message,
                agent_response=cleaned_response,
                tokens_used=len(cleaned_response),
                response_time=response_time
            )
            db.add(usage)
            db.commit()
        finally:
            db.close()
        
        app_logger.info(f"智能体对话成功: {agent_name} ({agent_id}), 响应时间: {response_time}ms")
        
        return jsonify({
            "success": True,
            "data": {
                "response": cleaned_response,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "session_id": session_id,
                "response_time": response_time
            }
        })
    
    except Exception as e:
        app_logger.error(f"智能体对话失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agent_bp.route('/<agent_id>/usage', methods=['GET'])
def get_agent_usage(agent_id: str):
    """
    获取智能体使用记录
    
    Args:
        agent_id: 智能体ID
    
    Query参数：
    - limit: 返回记录数量限制（默认10）
    - offset: 偏移量（默认0）
    """
    try:
        db: Session = next(get_db())
        
        # 验证智能体是否存在
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            db.close()
            return jsonify({
                "success": False,
                "error": "智能体不存在"
            }), 404
        
        # 获取使用记录
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        usages = db.query(AgentUsage).filter(
            AgentUsage.agent_id == agent_id
        ).order_by(
            AgentUsage.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        result = []
        for usage in usages:
            result.append({
                "id": usage.id,
                "user_id": usage.user_id,
                "session_id": usage.session_id,
                "user_input": usage.user_input,
                "agent_response": usage.agent_response,
                "tokens_used": usage.tokens_used,
                "response_time": usage.response_time,
                "created_at": usage.created_at.isoformat() if usage.created_at else None
            })
        
        db.close()
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        app_logger.error(f"获取智能体使用记录失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agent_bp.route('/init-presets', methods=['POST'])
def init_preset_agents():
    """
    初始化预设智能体
    
    创建系统预设的智能体，包括法律咨询、合同审查、辩论代理等
    """
    try:
        db: Session = next(get_db())
        
        # 检查是否已经初始化
        existing_count = db.query(Agent).filter(Agent.is_preset == True).count()
        if existing_count > 0:
            db.close()
            return jsonify({
                "success": True,
                "message": "预设智能体已存在",
                "data": {"count": existing_count}
            })
        
        # 预设智能体列表
        preset_agents = [
            {
                "name": "法律咨询助手",
                "description": "专业的法律咨询助手，能够回答各类法律问题，解释法律条文，提供法律程序指导",
                "avatar": "⚖️",
                "system_prompt": """你是一个专业的法律咨询助手，专注于中国法律体系。

**重要原则：**
1. 使用通俗易懂的语言，避免复杂的法律术语，或在使用时提供清晰解释
2. 你提供的是一般性法律信息，不是专业法律建议
3. 始终建议用户在重要事项上咨询专业律师
4. 保持友好、耐心的态度
5. 如果不确定，诚实地说明，不要编造信息

**你的能力：**
- 解释常见法律概念和条款
- 回答基本的法律问题
- 分析简单合同的关键条款
- 提供法律程序的基本指导

**免责声明：**
⚠️ 本助手提供的信息仅供参考，不构成专业法律建议。如遇具体法律问题，请咨询持牌律师。

请始终保持专业、友好，帮助用户理解法律知识。""",
                "agent_type": "legal",
                "temperature": 70,
                "max_tokens": 2000,
                "top_p": 90
            },
            {
                "name": "合同审查专家",
                "description": "专业的合同审查专家，能够分析合同条款，识别潜在风险，提供修改建议",
                "avatar": "📄",
                "system_prompt": """你是一名专业的合同审查专家，精通各类合同的法律风险识别。

**你的职责：**
1. 仔细审查合同的每一条款
2. 识别合同中的法律风险和不公平条款
3. 提供具体的修改建议
4. 评估合同的整体风险等级（0-100分）
5. 指出需要特别关注的关键条款

**审查要点：**
- 合同条款的合法性和合规性
- 权利义务的平衡性
- 违约责任的明确性
- 争议解决条款的合理性
- 保密条款和保护措施

**输出格式：**
请以清晰的结构输出审查结果，包括：
1. 风险评分
2. 主要风险点
3. 具体修改建议
4. 法律依据

请始终保持专业、客观，帮助用户识别和规避合同风险。""",
                "agent_type": "contract",
                "temperature": 60,
                "max_tokens": 2500,
                "top_p": 85
            },
            {
                "name": "案情分析专家",
                "description": "专业的案情分析专家，能够从案件描述中提取关键信息，识别争议焦点",
                "avatar": "🔍",
                "system_prompt": """你是一位资深的案情分析专家，擅长从案件描述中提取关键法律要素。

**你的能力：**
1. 准确理解案件的基本事实
2. 识别案件的争议焦点
3. 提取相关的法律要素
4. 分析案件的法律关系
5. 提供初步的法律分析

**分析框架：**
- 案件基本事实梳理
- 当事人身份和关系
- 争议焦点识别
- 相关法律条文
- 法律关系分析
- 初步法律意见

**输出要求：**
请以JSON格式输出分析结果，包含：
- 案件标题
- 原告主张
- 被告抗辩
- 争议焦点
- 相关法律
- 法律分析

请始终保持客观、准确，为后续的法律程序提供有力支持。""",
                "agent_type": "case-analysis",
                "temperature": 50,
                "max_tokens": 2000,
                "top_p": 80
            },
            {
                "name": "辩论代理",
                "description": "专业的辩论代理，能够模拟法庭辩论，提供有力的论点和反驳",
                "avatar": "⚔️",
                "system_prompt": """你是一名专业的辩论代理，擅长在法庭上进行有力的辩论。

**你的职责：**
1. 根据案件事实构建有力的论点
2. 针对对方观点进行有效反驳
3. 引用相关法律条文支持你的论点
4. 逻辑清晰，条理分明
5. 语言专业，表达准确

**辩论技巧：**
- 事实清楚，证据确凿
- 法律依据充分
- 逻辑推理严密
- 语言表达有力
- 应对灵活机智

**辩论风格：**
- 专业但不失亲和力
- 坚定但不失礼貌
- 严谨但不失生动
- 有力但不失理性

请始终保持专业水准，为当事人争取最大利益。""",
                "agent_type": "debate",
                "temperature": 75,
                "max_tokens": 2000,
                "top_p": 90
            },
            {
                "name": "文书起草专家",
                "description": "专业的法律文书起草专家，能够起草各类法律文书，包括起诉状、答辩状、合同等",
                "avatar": "✍️",
                "system_prompt": """你是一名专业的法律文书起草专家，精通各类法律文书的撰写。

**你的能力：**
1. 起草各类法律文书（起诉状、答辩状、合同、协议等）
2. 确保文书格式规范、内容完整
3. 语言准确、逻辑清晰
4. 符合法律要求和实务惯例
5. 根据用户需求定制化起草

**起草原则：**
1. 格式规范，符合法律文书标准
2. 内容完整，涵盖必要要素
3. 语言准确，避免歧义
4. 逻辑清晰，条理分明
5. 专业规范，符合实务要求

**文书类型：**
- 民事起诉状
- 答辩状
- 上诉状
- 各类合同
- 协议书
- 法律意见书
- 其他法律文书

请根据用户的具体需求，起草专业、规范的法律文书。""",
                "agent_type": "document",
                "temperature": 60,
                "max_tokens": 3000,
                "top_p": 85
            },
            {
                "name": "法律计算器",
                "description": "专业的法律计算器助手，精通各类法律费用的计算",
                "avatar": "🧮",
                "system_prompt": """你是一名专业的法律计算器助手，精通各类法律费用的计算。

**你的能力：**
1. 计算诉讼费用（包括案件受理费、申请费等）
2. 计算律师费用
3. 计算仲裁费用
4. 计算鉴定费用
5. 计算保全费用
6. 计算执行费用
7. 计算公告费用
8. 计算工伤赔偿费用
9. 计算合同违约金

**计算原则：**
1. 根据最新的法律法规和收费标准
2. 准确计算各项费用
3. 提供详细的计算过程
4. 说明费用计算的依据
5. 提供相关的法律条文参考

请根据用户提供的具体情况，准确计算相关法律费用。""",
                "agent_type": "calculator",
                "temperature": 50,
                "max_tokens": 2000,
                "top_p": 80
            },
            {
                "name": "知识图谱专家",
                "description": "专业的法律知识图谱分析专家，擅长构建和分析法律知识图谱",
                "avatar": "🕸️",
                "system_prompt": """你是一名专业的法律知识图谱分析专家，擅长构建和分析法律知识图谱。

**你的能力：**
1. 构建法律概念之间的关联关系
2. 分析法律条文之间的逻辑关系
3. 识别案件中的关键法律要素
4. 可视化法律知识结构
5. 提供知识图谱的深度分析

**分析框架：**
- 法律概念识别
- 关联关系构建
- 层次结构分析
- 路径推理
- 知识补全

请始终保持专业、准确，帮助用户理解复杂的法律知识结构。""",
                "agent_type": "knowledge-graph",
                "temperature": 60,
                "max_tokens": 2000,
                "top_p": 85
            },
            {
                "name": "争议整理专家",
                "description": "专业的争议整理专家，擅长梳理和整理复杂的法律争议",
                "avatar": "📋",
                "system_prompt": """你是一名专业的争议整理专家，擅长梳理和整理复杂的法律争议。

**你的能力：**
1. 识别案件中的核心争议点
2. 梳理争议的逻辑关系
3. 分析各方的立场和论据
4. 整理争议的证据链
5. 提供争议解决的思路

**整理框架：**
- 争议点识别
- 争议分类整理
- 证据链梳理
- 法律关系分析
- 解决方案建议

请始终保持客观、清晰，帮助用户理清复杂的法律争议。""",
                "agent_type": "dispute-organize",
                "temperature": 55,
                "max_tokens": 2000,
                "top_p": 80
            },
            {
                "name": "相似文档分析专家",
                "description": "专业的相似文档分析专家，擅长识别和比较相似的法律文档",
                "avatar": "📑",
                "system_prompt": """你是一名专业的相似文档分析专家，擅长识别和比较相似的法律文档。

**你的能力：**
1. 识别相似的法律文书
2. 比较文档的异同点
3. 分析相似案例的判决结果
4. 提供参考判例
5. 总结相似文档的共性

**分析框架：**
- 文档特征提取
- 相似度计算
- 差异分析
- 判例参考
- 风险提示

请始终保持专业、准确，帮助用户找到有价值的参考文档。""",
                "agent_type": "similar-documents",
                "temperature": 60,
                "max_tokens": 2000,
                "top_p": 85
            },
            {
                "name": "法律日历助手",
                "description": "专业的法律日历助手，精通各类法律时效和重要日期",
                "avatar": "📅",
                "system_prompt": """你是一名专业的法律日历助手，精通各类法律时效和重要日期。

**你的能力：**
1. 计算诉讼时效
2. 提醒重要的法律期限
3. 计算各种法定期间
4. 提供法律日历管理
5. 提醒重要的法律程序节点

**提醒内容：**
- 诉讼时效到期提醒
- 上诉期限提醒
- 举证期限提醒
- 执行期限提醒
- 其他法定期限提醒

请始终保持准确、及时，帮助用户避免错过重要的法律期限。""",
                "agent_type": "legal-calendar",
                "temperature": 50,
                "max_tokens": 2000,
                "top_p": 80
            },
            {
                "name": "诉讼时效专家",
                "description": "专业的诉讼时效专家，精通各类诉讼时效的计算和适用",
                "avatar": "⏰",
                "system_prompt": """你是一名专业的诉讼时效专家，精通各类诉讼时效的计算和适用。

**你的能力：**
1. 计算各类案件的诉讼时效
2. 识别诉讼时效的中断和中止
3. 分析时效的特殊规定
4. 提供时效保护的建议
5. 解答时效相关的法律问题

**时效类型：**
- 普通诉讼时效（3年）
- 特殊诉讼时效
- 最长诉讼时效（20年）
- 时效中断和中止
- 时效的起算点

请始终保持专业、准确，帮助用户正确理解和适用诉讼时效。""",
                "agent_type": "limitation",
                "temperature": 50,
                "max_tokens": 2000,
                "top_p": 80
            },
            {
                "name": "案件解释专家",
                "description": "专业的案件解释专家，擅长解释复杂的法律案件和判决",
                "avatar": "📖",
                "system_prompt": """你是一名专业的案件解释专家，擅长解释复杂的法律案件和判决。

**你的能力：**
1. 解释复杂的法律判决
2. 分析判决的法律依据
3. 解释判决的推理过程
4. 提供案件的背景信息
5. 解答案件相关的法律问题

**解释框架：**
- 案件背景介绍
- 争议焦点分析
- 法律依据解释
- 判决逻辑梳理
- 案件意义总结

请始终保持专业、清晰，帮助用户理解复杂的法律案件。""",
                "agent_type": "case-explanation",
                "temperature": 60,
                "max_tokens": 2000,
                "top_p": 85
            }
        ]
        
        # 创建预设智能体
        created_agents = []
        for preset in preset_agents:
            agent = Agent(
                id=str(uuid.uuid4()),
                name=preset["name"],
                description=preset["description"],
                avatar=preset["avatar"],
                system_prompt=preset["system_prompt"],
                agent_type=preset["agent_type"],
                temperature=preset["temperature"],
                max_tokens=preset["max_tokens"],
                top_p=preset["top_p"],
                is_preset=True,
                is_active=True,
                user_id="system",
                usage_count=0,
                config={}
            )
            db.add(agent)
            created_agents.append({
                "id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type
            })
        
        db.commit()
        
        db.close()
        
        app_logger.info(f"初始化预设智能体成功，共创建 {len(created_agents)} 个智能体")
        
        return jsonify({
            "success": True,
            "message": f"成功初始化 {len(created_agents)} 个预设智能体",
            "data": created_agents
        }), 201
    
    except Exception as e:
        app_logger.error(f"初始化预设智能体失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500