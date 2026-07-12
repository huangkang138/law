"""
数据库模型
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime, JSON, Float
from sqlalchemy.sql import func
from core.database import Base


class User(Base):
    """
    用户表
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Contract(Base):
    """
    合同表
    """
    __tablename__ = "contracts"
    
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    text_length = Column(Integer, nullable=False)
    overall_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ContractRisk(Base):
    """
    合同风险表
    """
    __tablename__ = "contract_risks"
    
    id = Column(String, primary_key=True, index=True)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    risk_level = Column(String, nullable=False)
    original_clause = Column(Text)
    original_text_quote = Column(Text)
    risk_explanation = Column(Text)
    legal_basis = Column(JSON)
    legal_basis_links = Column(JSON)
    revise_suggestion = Column(Text)
    confidence_score = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LegalChatSession(Base):
    """
    普法问答会话表
    """
    __tablename__ = "legal_chat_sessions"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    jurisdiction = Column(String, default="中国")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LegalChatMessage(Base):
    """
    普法问答消息表
    """
    __tablename__ = "legal_chat_messages"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("legal_chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user 或 assistant
    content = Column(Text, nullable=False)
    tokens = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Case(Base):
    """
    案件表
    """
    __tablename__ = "cases"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    case_type = Column(String, nullable=False)
    case_description = Column(Text, nullable=False)
    plaintiff_claims = Column(JSON)
    defendant_defenses = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CourtSession(Base):
    """
    庭审会话表
    """
    __tablename__ = "court_sessions"
    
    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    current_phase = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    verdict = Column(Text)
    reasoning = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Evidence(Base):
    """
    证据表
    """
    __tablename__ = "evidence"
    
    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    party = Column(String, nullable=False)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    evidence_type = Column(String, nullable=False)
    probative_force = Column(Integer, default=0)
    is_authenticated = Column(Boolean, default=False)
    authentication_opinion = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LegalIssue(Base):
    """
    法律争议点表
    """
    __tablename__ = "legal_issues"
    
    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    description = Column(Text, nullable=False)
    relevant_law = Column(Text)
    plaintiff_position = Column(Text)
    defendant_position = Column(Text)
    judge_analysis = Column(Text)
    conclusion = Column(Text)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DebateTurn(Base):
    """
    辩论回合表
    """
    __tablename__ = "debate_turns"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("court_sessions.id"), nullable=False)
    phase = Column(String, nullable=False)
    party = Column(String, nullable=False)
    speaker_role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    legal_basis = Column(JSON)
    facts_stated = Column(JSON)
    arguments_made = Column(JSON)
    counter_arguments = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class CaseAnalysis(Base):
    """
    案情推断记录表
    """
    __tablename__ = "case_analyses"
    
    id = Column(String, primary_key=True, index=True)
    case_description = Column(Text, nullable=False)
    analysis_result = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SimilarDocumentSearch(Base):
    """
    相似文书搜索记录表
    """
    __tablename__ = "similar_document_searches"
    
    id = Column(String, primary_key=True, index=True)
    document_content = Column(Text, nullable=False)
    search_result = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DisputeInfo(Base):
    """
    纠纷信息整理表
    """
    __tablename__ = "dispute_infos"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    parties = Column(JSON)
    event_time = Column(String)
    event_description = Column(Text, nullable=False)
    demands = Column(Text)
    evidence_list = Column(JSON)
    input_type = Column(String)
    raw_input = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EvidenceRecord(Base):
    """
    取证存证记录表
    """
    __tablename__ = "evidence_records"
    
    id = Column(String, primary_key=True, index=True)
    dispute_id = Column(String, ForeignKey("dispute_infos.id"))
    evidence_name = Column(String, nullable=False)
    evidence_type = Column(String, nullable=False)
    evidence_content = Column(Text)
    file_path = Column(String)
    collection_method = Column(Text)
    is_certified = Column(Boolean, default=False)
    certification_time = Column(DateTime(timezone=True))
    certification_id = Column(String)
    legal_validity = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RightsProtectionPath(Base):
    """
    维权路径规划表
    """
    __tablename__ = "rights_protection_paths"
    
    id = Column(String, primary_key=True, index=True)
    dispute_id = Column(String, ForeignKey("dispute_infos.id"))
    dispute_type = Column(String, nullable=False)
    recommended_path = Column(JSON)
    current_step = Column(Integer, default=0)
    selected_path = Column(String)
    required_materials = Column(JSON)
    estimated_time = Column(String)
    estimated_cost = Column(String)
    success_rate = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LegalDocument(Base):
    """
    法律文书生成表
    """
    __tablename__ = "legal_documents"
    
    id = Column(String, primary_key=True, index=True)
    dispute_id = Column(String, ForeignKey("dispute_infos.id"))
    document_type = Column(String, nullable=False)
    document_title = Column(String, nullable=False)
    document_content = Column(Text, nullable=False)
    is_submitted = Column(Boolean, default=False)
    submit_time = Column(DateTime(timezone=True))
    submit_court = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CasePrediction(Base):
    """
    同类案件预判表
    """
    __tablename__ = "case_predictions"
    
    id = Column(String, primary_key=True, index=True)
    dispute_id = Column(String, ForeignKey("dispute_infos.id"))
    similar_cases = Column(JSON)
    win_probability = Column(Integer)
    predicted_amount = Column(String)
    court_tendency = Column(Text)
    optimization_suggestions = Column(Text)
    risk_analysis = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CaseReminder(Base):
    """
    案件流程提醒表
    """
    __tablename__ = "case_reminders"
    
    id = Column(String, primary_key=True, index=True)
    dispute_id = Column(String, ForeignKey("dispute_infos.id"))
    reminder_type = Column(String, nullable=False)
    reminder_time = Column(DateTime(timezone=True), nullable=False)
    reminder_content = Column(Text, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_time = Column(DateTime(timezone=True))
    prepared_materials = Column(JSON)
    prepared_scripts = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RiskWarning(Base):
    """
    避坑提醒表
    """
    __tablename__ = "risk_warnings"
    
    id = Column(String, primary_key=True, index=True)
    dispute_id = Column(String, ForeignKey("dispute_infos.id"))
    risk_summary = Column(Text, nullable=False)
    lessons_learned = Column(JSON)
    prevention_suggestions = Column(JSON)
    future_check_items = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LegalCase(Base):
    """
    法律案例表
    """
    __tablename__ = "legal_cases"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    case_number = Column(String, nullable=False)
    court = Column(String, nullable=False)
    date = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    keywords = Column(JSON)
    case_type = Column(String, nullable=False)
    similarity_score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CaseExplanationSearch(Base):
    """
    相似案件解释搜索记录表
    """
    __tablename__ = "case_explanation_searches"
    
    id = Column(String, primary_key=True, index=True)
    search_query = Column(Text, nullable=False)
    search_result = Column(Text, nullable=False)
    similar_cases = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DocumentDraft(Base):
    """
    文档起草记录表
    """
    __tablename__ = "document_drafts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, default='anonymous')
    document_type = Column(String(50), nullable=False)  # legal-document, contract-drafting, legal-opinion
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    result = Column(Text, nullable=True)
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    is_pinned = Column(Boolean, default=False)
    custom_title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LegalDocumentDraft(Base):
    """
    法律文书起草详情表
    """
    __tablename__ = "legal_document_drafts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(Integer, ForeignKey("document_drafts.id", ondelete="CASCADE"), nullable=False)
    template_type = Column(String(100), nullable=True)  # 文书模板类型
    case_summary = Column(Text, nullable=True)  # 案情概要
    uploaded_files = Column(JSON, nullable=True)  # 上传的文件列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ContractDraft(Base):
    """
    合同起草详情表
    """
    __tablename__ = "contract_drafts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(Integer, ForeignKey("document_drafts.id", ondelete="CASCADE"), nullable=False)
    contract_type = Column(String(100), nullable=True)  # 合同类型
    parties_info = Column(JSON, nullable=True)  # 合同双方信息
    contract_purpose = Column(Text, nullable=True)  # 合同目的
    terms_summary = Column(Text, nullable=True)  # 主要条款摘要
    uploaded_files = Column(JSON, nullable=True)  # 上传的文件列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LegalOpinionDraft(Base):
    """
    法律意见起草详情表
    """
    __tablename__ = "legal_opinion_drafts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(Integer, ForeignKey("document_drafts.id", ondelete="CASCADE"), nullable=False)
    current_step = Column(Integer, default=1)  # 当前步骤
    case_summary = Column(Text, nullable=True)  # 案情概要
    case_organized = Column(Text, nullable=True)  # 案情梳理结果
    analysis_focus = Column(Text, nullable=True)  # 分析重点
    selected_court = Column(String(255), nullable=True)  # 选择的法院
    uploaded_files = Column(JSON, nullable=True)  # 上传的文件列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class InterestCalculation(Base):
    """
    利息计算记录表
    """
    __tablename__ = "interest_calculations"
    
    id = Column(String, primary_key=True, index=True)
    principal = Column(String, nullable=False)
    annual_rate = Column(String, nullable=False)
    days = Column(Integer, nullable=False)
    interest = Column(String, nullable=False)
    total_amount = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LaborCompensation(Base):
    """
    劳动补偿计算记录表
    """
    __tablename__ = "labor_compensations"
    
    id = Column(String, primary_key=True, index=True)
    monthly_salary = Column(String, nullable=False)
    years = Column(Integer, nullable=False)
    months = Column(Integer, default=0)
    compensation = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TrafficAccidentCompensation(Base):
    """
    交通事故赔偿计算记录表
    """
    __tablename__ = "traffic_accident_compensations"
    
    id = Column(String, primary_key=True, index=True)
    medical_expense = Column(String, nullable=False)
    lost_income = Column(String, nullable=False)
    disability_level = Column(Integer, nullable=False)
    total_compensation = Column(String, nullable=False)
    details = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CourtFee(Base):
    """
    诉讼费用计算记录表
    """
    __tablename__ = "court_fees"
    
    id = Column(String, primary_key=True, index=True)
    case_type = Column(String, nullable=False)
    amount = Column(String, nullable=False)
    fee = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkInjuryCompensation(Base):
    """
    工伤赔偿计算记录表
    """
    __tablename__ = "work_injury_compensations"
    
    id = Column(String, primary_key=True, index=True)
    injury_level = Column(Integer, nullable=False)
    monthly_salary = Column(String, nullable=False)
    total_compensation = Column(String, nullable=False)
    details = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LawyerFee(Base):
    """
    律师费计算记录表
    """
    __tablename__ = "lawyer_fees"
    
    id = Column(String, primary_key=True, index=True)
    case_type = Column(String, nullable=False)
    amount = Column(String, nullable=False)
    fee_method = Column(String, nullable=False)
    fee = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LegalCalendarEvent(Base):
    """
    法律日历事件表
    """
    __tablename__ = "legal_calendar_events"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text)
    is_reminder = Column(Boolean, default=False)
    reminder_days = Column(Integer, default=7)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LimitationCheck(Base):
    """
    诉讼时效查询记录表
    """
    __tablename__ = "limitation_checks"
    
    id = Column(String, primary_key=True, index=True)
    case_type = Column(String, nullable=False)
    incident_date = Column(String, nullable=False)
    limitation_period = Column(Integer, nullable=False)
    expiration_date = Column(String, nullable=False)
    is_expired = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ContractPenalty(Base):
    """
    合同违约金计算记录表
    """
    __tablename__ = "contract_penalties"
    
    id = Column(String, primary_key=True, index=True)
    contract_amount = Column(String, nullable=False)
    penalty_rate = Column(String, nullable=False)
    delay_days = Column(Integer, nullable=False)
    penalty_amount = Column(String, nullable=False)
    total_amount = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PreservationFee(Base):
    """
    保全费计算记录表
    """
    __tablename__ = "preservation_fees"
    
    id = Column(String, primary_key=True, index=True)
    preservation_amount = Column(String, nullable=False)
    fee = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ExecutionFee(Base):
    """
    执行费计算记录表
    """
    __tablename__ = "execution_fees"
    
    id = Column(String, primary_key=True, index=True)
    execution_amount = Column(String, nullable=False)
    fee = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WillFee(Base):
    """
    遗嘱费用计算记录表
    """
    __tablename__ = "will_fees"
    
    id = Column(String, primary_key=True, index=True)
    estate_value = Column(String, nullable=False)
    will_type = Column(String, nullable=False)
    notary_fee = Column(String, nullable=False)
    attorney_fee = Column(String, nullable=False)
    total_fee = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnnouncementFee(Base):
    """
    公告费计算记录表
    """
    __tablename__ = "announcement_fees"
    
    id = Column(String, primary_key=True, index=True)
    announcement_type = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    times = Column(Integer, nullable=False)
    fee = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AppraisalFee(Base):
    """
    鉴定费计算记录表
    """
    __tablename__ = "appraisal_fees"
    
    id = Column(String, primary_key=True, index=True)
    appraisal_type = Column(String, nullable=False)
    subject_value = Column(String, nullable=False)
    fee = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ArbitrationFee(Base):
    """
    仲裁费计算记录表
    """
    __tablename__ = "arbitration_fees"
    
    id = Column(String, primary_key=True, index=True)
    arbitration_amount = Column(String, nullable=False)
    case_handling_fee = Column(String, nullable=False)
    arbitration_fee = Column(String, nullable=False)
    total_fee = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UMLDiagram(Base):
    """
    UML图表生成记录表
    """
    __tablename__ = "uml_diagrams"
    
    id = Column(String, primary_key=True, index=True)
    diagram_type = Column(String, nullable=False)  # plantuml, mermaid, graphviz
    diagram_source = Column(Text, nullable=False)
    output_format = Column(String, nullable=False)  # svg, png, pdf, jpeg
    output_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Favorite(Base):
    """
    收藏表
    """
    __tablename__ = "favorites"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, default='anonymous')
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    source_type = Column(String, nullable=False)  # legal, contract, debate, case-analysis, similar-documents, dispute, evidence, protection, document, prediction, reminder, warning, uml-diagram
    source_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Agent(Base):
    """
    智能体表
    """
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    avatar = Column(String)  # 智能体头像URL
    system_prompt = Column(Text, nullable=False)  # 系统提示词
    agent_type = Column(String, nullable=False)  # 智能体类型：legal, contract, debate, case-analysis, document, custom
    temperature = Column(Integer, default=70)  # 温度参数 (0-100)
    max_tokens = Column(Integer, default=2000)  # 最大token数
    top_p = Column(Integer, default=90)  # top_p参数 (0-100)
    is_preset = Column(Boolean, default=False)  # 是否为预设智能体
    is_active = Column(Boolean, default=True)  # 是否启用
    user_id = Column(String, nullable=False, default='anonymous')  # 创建者ID
    usage_count = Column(Integer, default=0)  # 使用次数
    config = Column(JSON)  # 额外配置参数
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AgentUsage(Base):
    """
    智能体使用记录表
    """
    __tablename__ = "agent_usages"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    user_id = Column(String, nullable=False, default='anonymous')
    session_id = Column(String)  # 会话ID
    user_input = Column(Text, nullable=False)  # 用户输入
    agent_response = Column(Text)  # 智能体响应
    tokens_used = Column(Integer)  # 使用的token数
    response_time = Column(Integer)  # 响应时间（毫秒）
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DigitalHumanSession(Base):
    """数字人会话表"""

    __tablename__ = "digital_human_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, default="anonymous", index=True)
    title = Column(String)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class DigitalHumanMessage(Base):
    """数字人消息表"""

    __tablename__ = "digital_human_messages"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(
        String,
        ForeignKey("digital_human_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    intent = Column(String)
    emotion = Column(String)
    confidence = Column(Float)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class DigitalHumanRequest(Base):
    """数字人请求幂等记录。"""

    __tablename__ = "digital_human_requests"

    request_id = Column(String, primary_key=True)
    client_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="processing")
    response_json = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Matter(Base):
    """Agent 任务工作区。"""

    __tablename__ = "matters"

    # Matter 是用户法律目标的工作区；阶段 1 只保存最小目标信息。
    id = Column(String, primary_key=True)
    client_id = Column(String, nullable=False, index=True)
    session_id = Column(String, ForeignKey("digital_human_sessions.id", ondelete="SET NULL"), index=True)
    title = Column(String, nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="active", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AgentRun(Base):
    """一次可暂停和恢复的 Agent 运行。"""

    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True)
    matter_id = Column(String, ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    current_step_id = Column(String, index=True)
    pending_approval_id = Column(String, index=True)
    # 完整状态快照用于服务重启后的恢复；可查询字段同时单独成列。
    state_json = Column(JSON, nullable=False, default=dict)
    error_code = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AgentStep(Base):
    """Agent 计划中的持久化步骤。"""

    __tablename__ = "agent_steps"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    # sequence 为后续多步骤计划预留稳定排序，阶段 1 固定为单步骤。
    sequence = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    tool_name = Column(String)
    error_code = Column(String)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ToolCall(Base):
    """受控工具调用及其结构化结果。"""

    __tablename__ = "tool_calls"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id = Column(String, ForeignKey("agent_steps.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    # 每次重试单独保存一条 ToolCall，避免覆盖失败证据。
    attempt = Column(Integer, nullable=False, default=1)
    input_json = Column(JSON, nullable=False, default=dict)
    result_json = Column(JSON)
    error_code = Column(String)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


class ApprovalRequest(Base):
    """需要用户明确确认后才能继续的审批。"""

    __tablename__ = "approval_requests"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    prompt = Column(Text, nullable=False)
    decision = Column(String)
    # 审批必须在有效期内且属于当前 client_id 才能恢复任务。
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    decided_at = Column(DateTime(timezone=True))


class AgentAuditEvent(Base):
    """面向审计的状态事件，不记录模型思维链。"""

    __tablename__ = "agent_audit_events"

    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    # 仅记录状态和动作摘要，不保存模型内部思维链。
    detail_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
