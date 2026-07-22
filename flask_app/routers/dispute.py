"""
纠纷处理相关路由
包括：纠纷信息整理、取证存证、维权路径规划、文书生成、案件预判、流程提醒、避坑提醒
"""

import os
import uuid
import json
from pathlib import Path
from flask import Blueprint, request, jsonify
from core.logger import app_logger
from services.material_extraction import extract_material_text

try:
    import cv2
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False
    app_logger.warning("opencv-python 未安装，视频文件处理功能不可用")

router = Blueprint('dispute', __name__)

# 上传文件存储目录
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def transcribe_audio(file_path: str) -> str:
    """
    转录音频文件为文本
    
    Args:
        file_path: 音频文件路径
        
    Returns:
        转录的文本内容
    """
    with open(file_path, "rb") as source:
        result = extract_material_text(os.path.basename(file_path), source)
    return f"[音频转录内容]: {result['text']}"


def extract_text_from_image(file_path: str) -> str:
    """
    从图片中提取文本
    
    Args:
        file_path: 图片文件路径
        
    Returns:
        提取的文本内容
    """
    with open(file_path, "rb") as source:
        result = extract_material_text(os.path.basename(file_path), source)
    return f"[图片文本内容]: {result['text']}"


def extract_frames_from_video(file_path: str) -> list:
    """
    从视频中提取关键帧
    
    Args:
        file_path: 视频文件路径
        
    Returns:
        提取的帧文件路径列表
    """
    if not VIDEO_AVAILABLE:
        return []
    
    try:
        app_logger.info(f"开始从视频提取帧: {file_path}")
        frames = []
        cap = cv2.VideoCapture(file_path)
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # 每10帧提取一帧
            if frame_count % 10 == 0:
                frame_path = os.path.join(UPLOAD_FOLDER, f"frame_{uuid.uuid4()}.jpg")
                cv2.imwrite(frame_path, frame)
                frames.append(frame_path)
            
            frame_count += 1
        
        cap.release()
        app_logger.info(f"视频帧提取成功，共提取 {len(frames)} 帧")
        return frames
    except Exception as e:
        app_logger.error(f"视频帧提取失败: {str(e)}")
        return []


def process_video(file_path: str) -> str:
    """
    处理视频文件
    
    Args:
        file_path: 视频文件路径
        
    Returns:
        处理后的文本内容
    """
    with open(file_path, "rb") as source:
        result = extract_material_text(os.path.basename(file_path), source)
    return f"[视频转录内容]: {result['text']}"


def _invoke_llm_streaming(messages: list) -> str:
    """
    使用流式传输调用LLM，避免长响应中断问题
    """
    import httpx
    import json
    from core.config import settings
    
    formatted_messages = []
    for msg in messages:
        app_logger.info(f"处理消息: {type(msg)}, 属性: {dir(msg)[:10]}")
        
        # 尝试多种方式获取消息类型和内容
        role = None
        content = None
        
        if hasattr(msg, '_type'):
            if msg._type == 'system':
                role = "system"
                content = msg.content
            elif msg._type == 'human':
                role = "user"
                content = msg.content
            elif msg._type == 'ai':
                role = "assistant"
                content = msg.content
        elif hasattr(msg, 'type'):
            if msg.type == 'system':
                role = "system"
                content = msg.content
            elif msg.type == 'human':
                role = "user"
                content = msg.content
            elif msg.type == 'ai':
                role = "assistant"
                content = msg.content
        elif hasattr(msg, 'role') and hasattr(msg, 'content'):
            role = msg.role
            content = msg.content
        elif isinstance(msg, dict):
            role = msg.get('role', 'user')
            content = msg.get('content', '')
        
        if role and content:
            formatted_messages.append({"role": role, "content": content})
            app_logger.info(f"添加消息: role={role}, content长度={len(content)}")
        else:
            app_logger.warning(f"无法处理消息: {msg}")
    
    app_logger.info(f"调用LLM - URL: {settings.OPENAI_BASE_URL}/chat/completions")
    
    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": formatted_messages,
        "temperature": float(settings.OPENAI_TEMPERATURE),
        "max_tokens": int(settings.OPENAI_MAX_TOKENS),
        "stream": True
    }
    
    app_logger.info(f"调用LLM - Payload: {json.dumps(payload, ensure_ascii=False)[:500]}...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
    }
    
    client = httpx.Client(timeout=180.0)
    content = ""
    
    try:
        with client.stream(
            "POST",
            f"{settings.OPENAI_BASE_URL}/chat/completions",
            json=payload,
            headers=headers
        ) as response:
            app_logger.info(f"LLM响应状态码: {response.status_code}")
            
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
            else:
                error_text = ""
                try:
                    for line in response.iter_lines():
                        if line:
                            error_text += line
                    error_data = json.loads(error_text) if error_text else {}
                    error_msg = error_data.get('error', {}).get('message', error_text[:200])
                except:
                    error_msg = error_text[:200] if error_text else f"状态码: {response.status_code}"
                app_logger.error(f"LLM调用失败: {response.status_code} - {error_msg}")
                content = "证据收集建议：1. 妥善保存原始证据材料；2. 确保证据的真实性和完整性；3. 按照法定程序收集证据；4. 注意证据的时效性。"
    except Exception as e:
        app_logger.error(f"LLM网络连接错误: {str(e)}")
        # 返回默认的证据收集建议
        content = "证据收集建议：1. 妥善保存原始证据材料；2. 确保证据的真实性和完整性；3. 按照法定程序收集证据；4. 注意证据的时效性。"
    finally:
        client.close()
    
    return content


# ==================== 纠纷信息整理接口 ====================

@router.route('/dispute/organize', methods=['POST'])
def organize_dispute():
    """
    纠纷信息整理接口
    
    根据用户输入的纠纷信息，AI自动整理成结构化的条目
    """
    try:
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        from core.database import get_db
        from models.db_models import DisputeInfo
        import uuid
        import json
        import os
        
        # 检查请求类型
        if 'multipart/form-data' in request.headers.get('Content-Type', ''):
            # 处理文件上传
            input_type = request.form.get('input_type', 'text')
            input_content = request.form.get('input_content', '')
            files = request.files.getlist('files')
            
            app_logger.info(f"开始整理纠纷信息，输入类型: {input_type}, 文件数量: {len(files)}")
            
            # 处理不同类型的文件
            if input_type == 'image' and files:
                # 处理图片文件
                image_contents = []
                for file in files:
                    # 保存文件
                    file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{file.filename}")
                    file.save(file_path)
                    # 提取图片文本
                    image_text = extract_text_from_image(file_path)
                    image_contents.append(image_text)
                    # 清理临时文件
                    try:
                        os.remove(file_path)
                    except:
                        pass
                input_content = "\n".join(image_contents)
            elif input_type == 'audio' and files:
                # 处理音频文件
                audio_file = files[0]
                file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{audio_file.filename}")
                audio_file.save(file_path)
                # 转录音频
                input_content = transcribe_audio(file_path)
                # 清理临时文件
                try:
                    os.remove(file_path)
                except:
                    pass
            elif input_type == 'video' and files:
                # 处理视频文件
                video_file = files[0]
                file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{video_file.filename}")
                video_file.save(file_path)
                # 处理视频
                input_content = process_video(file_path)
                # 清理临时文件
                try:
                    os.remove(file_path)
                except:
                    pass
        else:
            # 处理JSON请求
            data = request.json
            if not data or 'input_content' not in data:
                return jsonify({
                    "success": False,
                    "error": "缺少必要参数 input_content"
                }), 400
            
            input_content = data.get('input_content')
            input_type = data.get('input_type', 'text')
            
            app_logger.info(f"开始整理纠纷信息，输入类型: {input_type}")
        
        llm = LLMFactory.create_llm()
        
        # 根据输入类型定制提示词
        if input_type == 'image':
            organize_prompt = f"""你是一名资深的法律专家，请根据以下用户上传的图片内容，整理成结构化的纠纷信息条目：

图片内容：{input_content}

请根据图片中的实际文本内容，整理成结构化的纠纷信息条目。

请按照以下格式整理（JSON格式）：
{{
    "title": "纠纷标题（简短概括）",
    "parties": [
        {{
            "name": "当事人姓名",
            "role": "角色（原告/被告/第三人）",
            "contact": "联系方式"
        }}
    ],
    "event_time": "事件发生时间",
    "event_description": "事件详细描述",
    "demands": "当事人的诉求",
    "evidence_list": [
        {{
            "name": "证据名称",
            "type": "证据类型",
            "description": "证据描述"
        }}
    ]
}}

要求：
- 根据图片中的实际文本内容整理信息
- 不要总是返回交通事故模板
- 准确提取当事人信息
- 清晰描述事件经过
- 明确当事人的诉求
- 列出可能需要的证据
- 语言简洁、准确"""
        elif input_type == 'audio':
            organize_prompt = f"""你是一名资深的法律专家，请根据以下用户上传的音频转录内容，整理成结构化的纠纷信息条目：

音频转录内容：{input_content}

请根据音频中的实际对话内容，整理成结构化的纠纷信息条目。

请按照以下格式整理（JSON格式）：
{{
    "title": "纠纷标题（简短概括）",
    "parties": [
        {{
            "name": "当事人姓名",
            "role": "角色（原告/被告/第三人）",
            "contact": "联系方式"
        }}
    ],
    "event_time": "事件发生时间",
    "event_description": "事件详细描述",
    "demands": "当事人的诉求",
    "evidence_list": [
        {{
            "name": "证据名称",
            "type": "证据类型",
            "description": "证据描述"
        }}
    ]
}}

要求：
- 根据音频中的实际对话内容整理信息
- 不要总是返回交通事故模板
- 准确提取当事人信息
- 清晰描述事件经过
- 明确当事人的诉求
- 列出可能需要的证据
- 语言简洁、准确"""
        elif input_type == 'video':
            organize_prompt = f"""你是一名资深的法律专家，请根据以下用户上传的视频内容，整理成结构化的纠纷信息条目：

视频内容：{input_content}

请根据视频中的实际内容，整理成结构化的纠纷信息条目。

请按照以下格式整理（JSON格式）：
{{
    "title": "纠纷标题（简短概括）",
    "parties": [
        {{
            "name": "当事人姓名",
            "role": "角色（原告/被告/第三人）",
            "contact": "联系方式"
        }}
    ],
    "event_time": "事件发生时间",
    "event_description": "事件详细描述",
    "demands": "当事人的诉求",
    "evidence_list": [
        {{
            "name": "证据名称",
            "type": "证据类型",
            "description": "证据描述"
        }}
    ]
}}

要求：
- 根据视频中的实际内容整理信息
- 不要总是返回交通事故模板
- 准确提取当事人信息
- 清晰描述事件经过
- 明确当事人的诉求
- 列出可能需要的证据
- 语言简洁、准确"""
        else:
            organize_prompt = f"""你是一名资深的法律专家，请根据以下用户输入的纠纷信息，整理成结构化的条目：

{input_content}

请按照以下格式整理（JSON格式）：
{{
    "title": "纠纷标题（简短概括）",
    "parties": [
        {{"name": "当事人姓名", "role": "角色（原告/被告/第三人）", "contact": "联系方式"}}
    ],
    "event_time": "事件发生时间",
    "event_description": "事件详细描述",
    "demands": "当事人的诉求",
    "evidence_list": [
        {{"name": "证据名称", "type": "证据类型", "description": "证据描述"}}
    ]
}}

要求：
- 准确提取当事人信息
- 清晰描述事件经过
- 明确当事人的诉求
- 列出可能需要的证据
- 语言简洁、准确"""

        messages = [
            SystemMessage(content="你是一名资深的法律专家，精通各类纠纷的处理，擅长从杂乱的信息中提取关键要点。"),
            HumanMessage(content=organize_prompt)
        ]
        
        app_logger.info("正在整理纠纷信息（流式传输）...")
        result_content = _invoke_llm_streaming(messages)
        
        try:
            if '```json' in result_content:
                json_str = result_content.split('```json')[1].split('```')[0].strip()
            elif '```' in result_content:
                json_str = result_content.split('```')[1].split('```')[0].strip()
            else:
                json_str = result_content.strip()
            
            organized_data = json.loads(json_str)
        except:
            organized_data = {
                "title": "纠纷信息",
                "parties": [],
                "event_time": "",
                "event_description": input_content,
                "demands": "",
                "evidence_list": []
            }
        
        db = next(get_db())
        try:
            dispute_record = DisputeInfo(
                id=str(uuid.uuid4()),
                title=organized_data.get('title', ''),
                parties=organized_data.get('parties', []),
                event_time=organized_data.get('event_time', ''),
                event_description=organized_data.get('event_description', ''),
                demands=organized_data.get('demands', ''),
                evidence_list=organized_data.get('evidence_list', []),
                input_type=input_type,
                raw_input=input_content
            )
            db.add(dispute_record)
            db.commit()
            db.refresh(dispute_record)
            app_logger.info(f"纠纷信息已保存到数据库，ID: {dispute_record.id}")
        finally:
            db.close()
        
        return jsonify({
            "success": True,
            "dispute_id": dispute_record.id,
            "organized_data": organized_data
        })
        
    except Exception as e:
        app_logger.error(f"纠纷信息整理错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/dispute/history', methods=['GET'])
def get_dispute_history():
    """
    获取纠纷信息历史记录
    """
    try:
        from core.database import get_db
        from models.db_models import DisputeInfo
        
        db = next(get_db())
        try:
            disputes = db.query(DisputeInfo).order_by(DisputeInfo.created_at.desc()).all()
            
            history = []
            for dispute in disputes:
                history.append({
                    "id": dispute.id,
                    "title": dispute.title,
                    "parties": dispute.parties,
                    "event_time": dispute.event_time,
                    "event_description": dispute.event_description,
                    "demands": dispute.demands,
                    "evidence_list": dispute.evidence_list,
                    "input_type": dispute.input_type,
                    "created_at": dispute.created_at.isoformat(),
                    "updated_at": dispute.updated_at.isoformat()
                })
            
            return jsonify({
                "success": True,
                "history": history
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取纠纷信息历史记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/dispute/<dispute_id>', methods=['DELETE'])
def delete_dispute(dispute_id):
    """
    删除纠纷信息记录
    """
    try:
        from core.database import get_db
        from models.db_models import DisputeInfo, EvidenceRecord, RightsProtectionPath, LegalDocument, CasePrediction, CaseReminder, RiskWarning
        
        db = next(get_db())
        try:
            dispute = db.query(DisputeInfo).filter(DisputeInfo.id == dispute_id).first()
            if not dispute:
                return jsonify({
                    "success": False,
                    "error": "记录不存在"
                }), 404
            
            # 先删除所有引用该纠纷的记录
            # 删除取证存证记录
            db.query(EvidenceRecord).filter(EvidenceRecord.dispute_id == dispute_id).delete()
            # 删除维权路径规划记录
            db.query(RightsProtectionPath).filter(RightsProtectionPath.dispute_id == dispute_id).delete()
            # 删除法律文书记录
            db.query(LegalDocument).filter(LegalDocument.dispute_id == dispute_id).delete()
            # 删除案件预判记录
            db.query(CasePrediction).filter(CasePrediction.dispute_id == dispute_id).delete()
            # 删除案件流程提醒记录
            db.query(CaseReminder).filter(CaseReminder.dispute_id == dispute_id).delete()
            # 删除避坑提醒记录
            db.query(RiskWarning).filter(RiskWarning.dispute_id == dispute_id).delete()
            
            # 再删除纠纷信息记录
            db.delete(dispute)
            db.commit()
            
            app_logger.info(f"纠纷信息记录已删除，ID: {dispute_id}")
            
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除纠纷信息记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 取证存证接口 ====================

@router.route('/evidence/collect', methods=['POST'])
def collect_evidence():
    """
    取证存证接口
    
    根据纠纷信息，指导用户收集证据并进行司法存证
    """
    try:
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        from core.database import get_db
        from models.db_models import DisputeInfo, EvidenceRecord
        import uuid
        import json
        
        data = request.json
        dispute_id = data.get('dispute_id')
        evidence_name = data.get('evidence_name')
        evidence_type = data.get('evidence_type')
        evidence_content = data.get('evidence_content')
        
        if not dispute_id:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 dispute_id"
            }), 400
        
        app_logger.info(f"开始取证存证，纠纷ID: {dispute_id}")
        
        db = next(get_db())
        try:
            dispute = db.query(DisputeInfo).filter(DisputeInfo.id == dispute_id).first()
            if not dispute:
                return jsonify({
                    "success": False,
                    "error": "纠纷信息不存在"
                }), 404
            
            llm = LLMFactory.create_llm()
            
            collect_prompt = f"""你是一名资深的法律专家，请根据以下纠纷信息和证据，提供取证指导：

纠纷描述：{dispute.event_description}
当事人诉求：{dispute.demands}
证据名称：{evidence_name}
证据类型：{evidence_type}
证据内容：{evidence_content}

请提供：
1. **取证方法**：如何合法有效地收集这份证据
2. **存证建议**：如何进行司法存证以确保法律效力
3. **注意事项**：取证过程中需要注意的法律风险
4. **证明力评估**：这份证据对案件的证明力如何"""

            messages = [
                SystemMessage(content="你是一名资深的法律专家，精通证据收集和司法存证。"),
                HumanMessage(content=collect_prompt)
            ]
            
            guidance = _invoke_llm_streaming(messages)
            
            evidence_record = EvidenceRecord(
                id=str(uuid.uuid4()),
                dispute_id=dispute_id,
                evidence_name=evidence_name,
                evidence_type=evidence_type,
                evidence_content=evidence_content,
                collection_method=guidance,
                is_certified=False
            )
            db.add(evidence_record)
            db.commit()
            db.refresh(evidence_record)
            
            app_logger.info(f"取证存证记录已保存，ID: {evidence_record.id}")
            
            return jsonify({
                "success": True,
                "evidence_id": evidence_record.id,
                "guidance": guidance
            })
        finally:
            db.close()
        
    except Exception as e:
        app_logger.error(f"取证存证错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/evidence/history', methods=['GET'])
def get_evidence_history():
    """
    获取取证存证历史记录
    """
    try:
        from core.database import get_db
        from models.db_models import EvidenceRecord
        
        db = next(get_db())
        try:
            evidences = db.query(EvidenceRecord).order_by(EvidenceRecord.created_at.desc()).all()
            
            history = []
            for evidence in evidences:
                history.append({
                    "id": evidence.id,
                    "dispute_id": evidence.dispute_id,
                    "evidence_name": evidence.evidence_name,
                    "evidence_type": evidence.evidence_type,
                    "evidence_content": evidence.evidence_content,
                    "collection_method": evidence.collection_method,
                    "is_certified": evidence.is_certified,
                    "certification_time": evidence.certification_time.isoformat() if evidence.certification_time else None,
                    "created_at": evidence.created_at.isoformat(),
                    "updated_at": evidence.updated_at.isoformat()
                })
            
            return jsonify({
                "success": True,
                "history": history
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取取证存证历史记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/evidence/<evidence_id>', methods=['DELETE'])
def delete_evidence(evidence_id):
    """
    删除取证存证记录
    """
    try:
        from core.database import get_db
        from models.db_models import EvidenceRecord
        
        db = next(get_db())
        try:
            evidence = db.query(EvidenceRecord).filter(EvidenceRecord.id == evidence_id).first()
            if not evidence:
                return jsonify({
                    "success": False,
                    "error": "记录不存在"
                }), 404
            
            db.delete(evidence)
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除取证存证记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 维权路径规划接口 ====================

@router.route('/protection/plan', methods=['POST'])
def plan_protection():
    """
    维权路径规划接口
    
    根据纠纷信息，规划维权路径
    """
    try:
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        from core.database import get_db
        from models.db_models import DisputeInfo, RightsProtectionPath
        import uuid
        import json
        
        data = request.json
        dispute_id = data.get('dispute_id')
        
        if not dispute_id:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 dispute_id"
            }), 400
        
        app_logger.info(f"开始规划维权路径，纠纷ID: {dispute_id}")
        
        db = next(get_db())
        try:
            dispute = db.query(DisputeInfo).filter(DisputeInfo.id == dispute_id).first()
            if not dispute:
                return jsonify({
                    "success": False,
                    "error": "纠纷信息不存在"
                }), 404
            
            llm = LLMFactory.create_llm()
            
            plan_prompt = f"""你是一名资深的法律专家，请根据以下纠纷信息，规划维权路径：

纠纷描述：{dispute.event_description}
当事人诉求：{dispute.demands}

请提供维权路径规划（JSON格式）：
{{
    "dispute_type": "纠纷类型",
    "recommended_path": [
        {{
            "step": 1,
            "action": "协商",
            "description": "与对方协商解决",
            "required_materials": ["材料1", "材料2"],
            "estimated_time": "1-2周",
            "estimated_cost": "免费"
        }}
    ],
    "success_rate": 70,
    "key_points": ["关键点1", "关键点2"]
}}

要求：
- 提供完整的维权路径
- 每一步都要有明确的操作指引
- 评估成功率和时间成本"""

            messages = [
                SystemMessage(content="你是一名资深的法律专家，精通各类纠纷的维权路径规划。"),
                HumanMessage(content=plan_prompt)
            ]
            
            result_content = _invoke_llm_streaming(messages)
            
            try:
                if '```json' in result_content:
                    json_str = result_content.split('```json')[1].split('```')[0].strip()
                elif '```' in result_content:
                    json_str = result_content.split('```')[1].split('```')[0].strip()
                else:
                    json_str = result_content.strip()
                
                plan_data = json.loads(json_str)
            except:
                plan_data = {
                    "dispute_type": "民事纠纷",
                    "recommended_path": [],
                    "success_rate": 50
                }
            
            path_record = RightsProtectionPath(
                id=str(uuid.uuid4()),
                dispute_id=dispute_id,
                dispute_type=plan_data.get('dispute_type', ''),
                recommended_path=plan_data.get('recommended_path', []),
                success_rate=plan_data.get('success_rate', 50)
            )
            db.add(path_record)
            db.commit()
            db.refresh(path_record)
            
            app_logger.info(f"维权路径规划已保存，ID: {path_record.id}")
            
            return jsonify({
                "success": True,
                "path_id": path_record.id,
                "plan_data": plan_data
            })
        finally:
            db.close()
        
    except Exception as e:
        app_logger.error(f"维权路径规划错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/protection/history', methods=['GET'])
def get_protection_history():
    """
    获取维权路径规划历史记录
    """
    try:
        from core.database import get_db
        from models.db_models import RightsProtectionPath
        
        db = next(get_db())
        try:
            paths = db.query(RightsProtectionPath).order_by(RightsProtectionPath.created_at.desc()).all()
            
            history = []
            for path in paths:
                history.append({
                    "id": path.id,
                    "dispute_id": path.dispute_id,
                    "dispute_type": path.dispute_type,
                    "recommended_path": path.recommended_path,
                    "current_step": path.current_step,
                    "selected_path": path.selected_path,
                    "success_rate": path.success_rate,
                    "created_at": path.created_at.isoformat(),
                    "updated_at": path.updated_at.isoformat()
                })
            
            return jsonify({
                "success": True,
                "history": history
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取维权路径规划历史记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/protection/<path_id>', methods=['DELETE'])
def delete_protection(path_id):
    """
    删除维权路径规划记录
    """
    try:
        from core.database import get_db
        from models.db_models import RightsProtectionPath
        
        db = next(get_db())
        try:
            path = db.query(RightsProtectionPath).filter(RightsProtectionPath.id == path_id).first()
            if not path:
                return jsonify({
                    "success": False,
                    "error": "记录不存在"
                }), 404
            
            db.delete(path)
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除维权路径规划记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 法律文书生成接口 ====================

@router.route('/document/generate', methods=['POST'])
def generate_document():
    """
    法律文书生成接口
    
    根据纠纷信息，自动生成法律文书
    """
    try:
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        from core.database import get_db
        from models.db_models import DisputeInfo, LegalDocument
        import uuid
        
        data = request.json
        dispute_id = data.get('dispute_id')
        document_type = data.get('document_type', '起诉状')
        
        if not dispute_id:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 dispute_id"
            }), 400
        
        app_logger.info(f"开始生成法律文书，纠纷ID: {dispute_id}，文书类型: {document_type}")
        
        db = next(get_db())
        try:
            dispute = db.query(DisputeInfo).filter(DisputeInfo.id == dispute_id).first()
            if not dispute:
                return jsonify({
                    "success": False,
                    "error": "纠纷信息不存在"
                }), 404
            
            llm = LLMFactory.create_llm()
            
            generate_prompt = f"""你是一名资深的法律专家，请根据以下纠纷信息，生成一份{document_type}：

纠纷标题：{dispute.title}
当事人信息：{dispute.parties}
事件时间：{dispute.event_time}
事件描述：{dispute.event_description}
当事人诉求：{dispute.demands}
证据列表：{dispute.evidence_list}

请直接生成{document_type}正文，不要添加任何引言或开场白，包括：
1. 标题
2. 当事人信息
3. 诉讼请求/申请事项
4. 事实与理由
5. 证据清单
6. 此致
7. 落款

要求：
- 格式规范，符合法律文书标准
- 内容完整，逻辑清晰
- 引用相关法律条文
- 语言专业、严谨
- 直接开始文书内容，不要有任何引言"""

            messages = [
                SystemMessage(content="你是一名资深的法律专家，精通各类法律文书的撰写。"),
                HumanMessage(content=generate_prompt)
            ]
            
            document_content = _invoke_llm_streaming(messages)
            
            # 移除不需要的引言
            unwanted_intro = "好的，作为一名资深的法律专家，我将根据您提供的纠纷信息，并结合法律实务要求，为您草拟一份规范的民事起诉状。"
            if unwanted_intro in document_content:
                document_content = document_content.replace(unwanted_intro, "")
            
            # 移除其他可能的引言
            intro_patterns = [
                "作为一名资深的法律专家",
                "根据您提供的纠纷信息",
                "为您草拟一份规范的"
            ]
            for pattern in intro_patterns:
                if pattern in document_content:
                    # 找到第一个句号或换行符，从那里开始截取
                    first_punctuation = document_content.find('。')
                    first_newline = document_content.find('\n')
                    cut_point = -1
                    if first_punctuation != -1:
                        cut_point = first_punctuation + 1
                    elif first_newline != -1:
                        cut_point = first_newline
                    if cut_point != -1:
                        document_content = document_content[cut_point:].strip()
            
            document_record = LegalDocument(
                id=str(uuid.uuid4()),
                dispute_id=dispute_id,
                document_type=document_type,
                document_title=f"{dispute.title}{document_type}",
                document_content=document_content
            )
            db.add(document_record)
            db.commit()
            db.refresh(document_record)
            
            app_logger.info(f"法律文书已生成并保存，ID: {document_record.id}")
            
            return jsonify({
                "success": True,
                "document_id": document_record.id,
                "document_content": document_content
            })
        finally:
            db.close()
        
    except Exception as e:
        app_logger.error(f"法律文书生成错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/document/history', methods=['GET'])
def get_document_history():
    """
    获取法律文书历史记录
    """
    try:
        from core.database import get_db
        from models.db_models import LegalDocument
        
        db = next(get_db())
        try:
            documents = db.query(LegalDocument).order_by(LegalDocument.created_at.desc()).all()
            
            history = []
            for doc in documents:
                history.append({
                    "id": doc.id,
                    "dispute_id": doc.dispute_id,
                    "document_type": doc.document_type,
                    "document_title": doc.document_title,
                    "document_content": doc.document_content[:200] + "..." if len(doc.document_content) > 200 else doc.document_content,
                    "is_submitted": doc.is_submitted,
                    "created_at": doc.created_at.isoformat(),
                    "updated_at": doc.updated_at.isoformat()
                })
            
            return jsonify({
                "success": True,
                "history": history
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取法律文书历史记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/document/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    """
    删除法律文书记录
    """
    try:
        from core.database import get_db
        from models.db_models import LegalDocument
        
        db = next(get_db())
        try:
            doc = db.query(LegalDocument).filter(LegalDocument.id == document_id).first()
            if not doc:
                return jsonify({
                    "success": False,
                    "error": "记录不存在"
                }), 404
            
            db.delete(doc)
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除法律文书记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 案件预判接口 ====================

@router.route('/prediction/analyze', methods=['POST'])
def analyze_prediction():
    """
    同类案件预判接口
    
    分析相似案例，预测案件结果
    """
    try:
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        from core.database import get_db
        from models.db_models import DisputeInfo, CasePrediction
        import uuid
        import json
        
        data = request.json
        dispute_id = data.get('dispute_id')
        
        if not dispute_id:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 dispute_id"
            }), 400
        
        app_logger.info(f"开始案件预判分析，纠纷ID: {dispute_id}")
        
        db = next(get_db())
        try:
            dispute = db.query(DisputeInfo).filter(DisputeInfo.id == dispute_id).first()
            if not dispute:
                return jsonify({
                    "success": False,
                    "error": "纠纷信息不存在"
                }), 404
            
            llm = LLMFactory.create_llm()
            
            prediction_prompt = f"""你是一名资深的法律专家，请根据以下纠纷信息，进行案件预判分析：

纠纷描述：{dispute.event_description}
当事人诉求：{dispute.demands}
证据列表：{dispute.evidence_list}

请提供案件预判分析（JSON格式）：
{{
    "similar_cases": [
        {{
            "case_name": "案例名称",
            "court": "审理法院",
            "date": "判决日期",
            "result": "判决结果",
            "similarity": 85
        }}
    ],
    "win_probability": 70,
    "predicted_amount": "预计赔偿金额",
    "court_tendency": "法院裁判倾向分析",
    "optimization_suggestions": "优化建议",
    "risk_analysis": "风险分析"
}}

要求：
- 分析3-5个相似案例
- 评估胜诉概率
- 预测可能的赔偿金额
- 提供优化建议"""

            messages = [
                SystemMessage(content="你是一名资深的法律专家，精通案例分析和案件预判。"),
                HumanMessage(content=prediction_prompt)
            ]
            
            result_content = _invoke_llm_streaming(messages)
            
            try:
                if '```json' in result_content:
                    json_str = result_content.split('```json')[1].split('```')[0].strip()
                elif '```' in result_content:
                    json_str = result_content.split('```')[1].split('```')[0].strip()
                else:
                    json_str = result_content.strip()
                
                prediction_data = json.loads(json_str)
            except:
                prediction_data = {
                    "similar_cases": [],
                    "win_probability": 50,
                    "predicted_amount": "无法预测",
                    "court_tendency": result_content,
                    "optimization_suggestions": "",
                    "risk_analysis": ""
                }
            
            prediction_record = CasePrediction(
                id=str(uuid.uuid4()),
                dispute_id=dispute_id,
                similar_cases=prediction_data.get('similar_cases', []),
                win_probability=prediction_data.get('win_probability', 50),
                predicted_amount=prediction_data.get('predicted_amount', ''),
                court_tendency=prediction_data.get('court_tendency', ''),
                optimization_suggestions=prediction_data.get('optimization_suggestions', ''),
                risk_analysis=prediction_data.get('risk_analysis', '')
            )
            db.add(prediction_record)
            db.commit()
            db.refresh(prediction_record)
            
            app_logger.info(f"案件预判分析已保存，ID: {prediction_record.id}")
            
            return jsonify({
                "success": True,
                "prediction_id": prediction_record.id,
                "prediction_data": prediction_data
            })
        finally:
            db.close()
        
    except Exception as e:
        app_logger.error(f"案件预判分析错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/prediction/history', methods=['GET'])
def get_prediction_history():
    """
    获取案件预判历史记录
    """
    try:
        from core.database import get_db
        from models.db_models import CasePrediction
        
        db = next(get_db())
        try:
            predictions = db.query(CasePrediction).order_by(CasePrediction.created_at.desc()).all()
            
            history = []
            for pred in predictions:
                history.append({
                    "id": pred.id,
                    "dispute_id": pred.dispute_id,
                    "similar_cases": pred.similar_cases,
                    "win_probability": pred.win_probability,
                    "predicted_amount": pred.predicted_amount,
                    "created_at": pred.created_at.isoformat(),
                    "updated_at": pred.updated_at.isoformat()
                })
            
            return jsonify({
                "success": True,
                "history": history
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取案件预判历史记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/prediction/<prediction_id>', methods=['DELETE'])
def delete_prediction(prediction_id):
    """
    删除案件预判记录
    """
    try:
        from core.database import get_db
        from models.db_models import CasePrediction
        
        db = next(get_db())
        try:
            pred = db.query(CasePrediction).filter(CasePrediction.id == prediction_id).first()
            if not pred:
                return jsonify({
                    "success": False,
                    "error": "记录不存在"
                }), 404
            
            db.delete(pred)
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除案件预判记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 案件流程提醒接口 ====================

@router.route('/reminder/create', methods=['POST'])
def create_reminder():
    """
    创建案件流程提醒
    
    根据纠纷信息，创建关键时间节点提醒
    """
    try:
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        from core.database import get_db
        from models.db_models import DisputeInfo, CaseReminder
        import uuid
        import json
        from datetime import datetime, timedelta
        
        data = request.json
        dispute_id = data.get('dispute_id')
        
        if not dispute_id:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 dispute_id"
            }), 400
        
        app_logger.info(f"开始创建案件流程提醒，纠纷ID: {dispute_id}")
        
        db = next(get_db())
        try:
            dispute = db.query(DisputeInfo).filter(DisputeInfo.id == dispute_id).first()
            if not dispute:
                return jsonify({
                    "success": False,
                    "error": "纠纷信息不存在"
                }), 404
            
            llm = LLMFactory.create_llm()
            
            reminder_prompt = f"""你是一名资深的法律专家，请根据以下纠纷信息，创建案件流程提醒：

纠纷描述：{dispute.event_description}
当事人诉求：{dispute.demands}

请提供案件流程提醒（JSON格式）：
{{
    "reminders": [
        {{
            "reminder_type": "立案提醒",
            "days_from_now": 7,
            "reminder_content": "提醒内容",
            "prepared_materials": ["材料1", "材料2"],
            "prepared_scripts": "准备的话术"
        }}
    ]
}}

要求：
- 创建3-5个关键时间节点的提醒
- 包括立案、举证、开庭、上诉等关键节点
- 每个提醒都要有准备材料和话术"""

            messages = [
                SystemMessage(content="你是一名资深的法律专家，精通案件流程管理。"),
                HumanMessage(content=reminder_prompt)
            ]
            
            result_content = _invoke_llm_streaming(messages)
            
            try:
                if '```json' in result_content:
                    json_str = result_content.split('```json')[1].split('```')[0].strip()
                elif '```' in result_content:
                    json_str = result_content.split('```')[1].split('```')[0].strip()
                else:
                    json_str = result_content.strip()
                
                reminder_data = json.loads(json_str)
            except:
                reminder_data = {"reminders": []}
            
            created_reminders = []
            for reminder_info in reminder_data.get('reminders', []):
                days = reminder_info.get('days_from_now', 7)
                reminder_time = datetime.now() + timedelta(days=days)
                
                reminder_record = CaseReminder(
                    id=str(uuid.uuid4()),
                    dispute_id=dispute_id,
                    reminder_type=reminder_info.get('reminder_type', ''),
                    reminder_time=reminder_time,
                    reminder_content=reminder_info.get('reminder_content', ''),
                    prepared_materials=reminder_info.get('prepared_materials', []),
                    prepared_scripts=reminder_info.get('prepared_scripts', '')
                )
                db.add(reminder_record)
                created_reminders.append({
                    "id": reminder_record.id,
                    "reminder_type": reminder_record.reminder_type,
                    "reminder_time": reminder_time.isoformat()
                })
            
            db.commit()
            
            app_logger.info(f"案件流程提醒已创建，数量: {len(created_reminders)}")
            
            return jsonify({
                "success": True,
                "reminders": created_reminders
            })
        finally:
            db.close()
        
    except Exception as e:
        app_logger.error(f"创建案件流程提醒错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/reminder/history', methods=['GET'])
def get_reminder_history():
    """
    获取案件流程提醒历史记录
    """
    try:
        from core.database import get_db
        from models.db_models import CaseReminder
        
        db = next(get_db())
        try:
            reminders = db.query(CaseReminder).order_by(CaseReminder.reminder_time.desc()).all()
            
            history = []
            for reminder in reminders:
                history.append({
                    "id": reminder.id,
                    "dispute_id": reminder.dispute_id,
                    "reminder_type": reminder.reminder_type,
                    "reminder_time": reminder.reminder_time.isoformat(),
                    "reminder_content": reminder.reminder_content,
                    "is_completed": reminder.is_completed,
                    "created_at": reminder.created_at.isoformat()
                })
            
            return jsonify({
                "success": True,
                "history": history
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取案件流程提醒历史记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/reminder/<reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    """
    删除案件流程提醒记录
    """
    try:
        from core.database import get_db
        from models.db_models import CaseReminder
        
        db = next(get_db())
        try:
            reminder = db.query(CaseReminder).filter(CaseReminder.id == reminder_id).first()
            if not reminder:
                return jsonify({
                    "success": False,
                    "error": "记录不存在"
                }), 404
            
            db.delete(reminder)
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除案件流程提醒记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 避坑提醒接口 ====================

@router.route('/warning/analyze', methods=['POST'])
def analyze_warning():
    """
    避坑提醒分析接口
    
    分析纠纷中的风险点，提供预防建议
    """
    try:
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        from core.database import get_db
        from models.db_models import DisputeInfo, RiskWarning
        import uuid
        import json
        
        data = request.json
        dispute_id = data.get('dispute_id')
        
        if not dispute_id:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 dispute_id"
            }), 400
        
        app_logger.info(f"开始避坑提醒分析，纠纷ID: {dispute_id}")
        
        db = next(get_db())
        try:
            dispute = db.query(DisputeInfo).filter(DisputeInfo.id == dispute_id).first()
            if not dispute:
                return jsonify({
                    "success": False,
                    "error": "纠纷信息不存在"
                }), 404
            
            llm = LLMFactory.create_llm()
            
            warning_prompt = f"""你是一名资深的法律专家，请根据以下纠纷信息，进行避坑提醒分析：

纠纷描述：{dispute.event_description}
当事人诉求：{dispute.demands}

请提供避坑提醒分析（JSON格式）：
{{
    "risk_summary": "风险总结",
    "lessons_learned": [
        "教训1：具体描述",
        "教训2：具体描述"
    ],
    "prevention_suggestions": [
        "预防建议1",
        "预防建议2"
    ],
    "future_check_items": [
        "未来检查项1：签合同时注意...",
        "未来检查项2：打借条时注意..."
    ]
}}

要求：
- 总结本次纠纷中的风险点
- 提炼经验教训
- 给出预防建议
- 列出未来需要注意的事项"""

            messages = [
                SystemMessage(content="你是一名资深的法律专家，擅长风险分析和预防。"),
                HumanMessage(content=warning_prompt)
            ]
            
            result_content = _invoke_llm_streaming(messages)
            
            try:
                if '```json' in result_content:
                    json_str = result_content.split('```json')[1].split('```')[0].strip()
                elif '```' in result_content:
                    json_str = result_content.split('```')[1].split('```')[0].strip()
                else:
                    json_str = result_content.strip()
                
                warning_data = json.loads(json_str)
            except:
                warning_data = {
                    "risk_summary": result_content,
                    "lessons_learned": [],
                    "prevention_suggestions": [],
                    "future_check_items": []
                }
            
            warning_record = RiskWarning(
                id=str(uuid.uuid4()),
                dispute_id=dispute_id,
                risk_summary=warning_data.get('risk_summary', ''),
                lessons_learned=warning_data.get('lessons_learned', []),
                prevention_suggestions=warning_data.get('prevention_suggestions', []),
                future_check_items=warning_data.get('future_check_items', [])
            )
            db.add(warning_record)
            db.commit()
            db.refresh(warning_record)
            
            app_logger.info(f"避坑提醒分析已保存，ID: {warning_record.id}")
            
            return jsonify({
                "success": True,
                "warning_id": warning_record.id,
                "warning_data": warning_data
            })
        finally:
            db.close()
        
    except Exception as e:
        app_logger.error(f"避坑提醒分析错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/warning/history', methods=['GET'])
def get_warning_history():
    """
    获取避坑提醒历史记录
    """
    try:
        from core.database import get_db
        from models.db_models import RiskWarning
        
        db = next(get_db())
        try:
            warnings = db.query(RiskWarning).order_by(RiskWarning.created_at.desc()).all()
            
            history = []
            for warning in warnings:
                history.append({
                    "id": warning.id,
                    "dispute_id": warning.dispute_id,
                    "risk_summary": warning.risk_summary,
                    "lessons_learned": warning.lessons_learned,
                    "prevention_suggestions": warning.prevention_suggestions,
                    "future_check_items": warning.future_check_items,
                    "created_at": warning.created_at.isoformat(),
                    "updated_at": warning.updated_at.isoformat()
                })
            
            return jsonify({
                "success": True,
                "history": history
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取避坑提醒历史记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/warning/<warning_id>', methods=['DELETE'])
def delete_warning(warning_id):
    """
    删除避坑提醒记录
    """
    try:
        from core.database import get_db
        from models.db_models import RiskWarning
        
        db = next(get_db())
        try:
            warning = db.query(RiskWarning).filter(RiskWarning.id == warning_id).first()
            if not warning:
                return jsonify({
                    "success": False,
                    "error": "记录不存在"
                }), 404
            
            db.delete(warning)
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除避坑提醒记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
