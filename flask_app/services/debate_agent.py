"""
辩论代理服务
"""

from flask_app.core.logger import app_logger
from flask_app.services.llm_factory import LLMFactory


class DebateAgent:
    """
    辩论代理
    """
    
    def __init__(self):
        """
        初始化辩论代理
        """
        self.llm = LLMFactory.create_llm()
        app_logger.info("✅ 辩论代理初始化完成")
    
    def start_debate(self, case_description: str, plaintiff_arguments: str = None, defendant_arguments: str = None) -> dict:
        """
        开始辩论
        
        Args:
            case_description: 案件描述
            plaintiff_arguments: 原告论据
            defendant_arguments: 被告论据
            
        Returns:
            辩论结果
        """
        try:
            # 构建提示词
            prompt = f"""
            你是一名法官，请对以下案件进行审理：
            
            案件描述：
            {case_description}
            
            原告论据：
            {plaintiff_arguments or "原告认为被告违反了合同约定，应当承担违约责任。"}
            
            被告论据：
            {defendant_arguments or "被告认为原告的主张没有法律依据，请求驳回原告诉讼请求。"}
            
            请基于法律规定和案件事实，给出法官意见。
            """
            
            # 调用 LLM
            response = self.llm.invoke(prompt)
            
            # 构建结果
            debate_result = {
                "case_description": case_description,
                "plaintiff_arguments": plaintiff_arguments or "原告认为被告违反了合同约定，应当承担违约责任。",
                "defendant_arguments": defendant_arguments or "被告认为原告的主张没有法律依据，请求驳回原告诉讼请求。",
                "judge_opinion": response.content
            }
            
            return debate_result
            
        except Exception as e:
            app_logger.error(f"辩论错误: {str(e)}")
            raise


# 单例实例
_debate_agent = None


def get_debate_agent() -> DebateAgent:
    """
    获取辩论代理实例
    """
    global _debate_agent
    if _debate_agent is None:
        _debate_agent = DebateAgent()
    return _debate_agent
