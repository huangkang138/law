"""
合同审查服务
"""

from flask_app.core.logger import app_logger
from flask_app.services.llm_factory import LLMFactory


class ContractReviewer:
    """
    合同审查器
    """
    
    def __init__(self):
        """
        初始化合同审查器
        """
        self.llm = LLMFactory.create_llm()
        app_logger.info("✅ 合同审查器初始化完成")
    
    def review_contract(self, contract_text: str) -> dict:
        """
        审查合同
        
        Args:
            contract_text: 合同文本
            
        Returns:
            审查结果
        """
        try:
            # 构建提示词
            prompt = f"""
            你是一名专业的法律顾问，请对以下合同进行审查：
            
            {contract_text}
            
            请从以下几个方面进行审查：
            1. 合同条款是否合法合规
            2. 是否存在不公平条款
            3. 是否存在潜在风险
            4. 建议修改的内容
            
            请提供详细的审查报告，包括风险评分（0-100）和具体修改建议。
            """
            
            # 调用 LLM
            response = self.llm.invoke(prompt)
            
            # 解析结果
            review_result = {
                "analysis": response.content,
                "risk_level": "medium",
                "key_clauses": []
            }
            
            # 模拟风险评分
            risk_score = 65
            
            # 模拟建议
            suggestions = [
                "建议明确试用期工资标准",
                "建议添加竞业限制条款",
                "建议细化违约责任"
            ]
            
            return {
                "review_result": review_result,
                "risk_score": risk_score,
                "suggestions": suggestions
            }
            
        except Exception as e:
            app_logger.error(f"合同审查错误: {str(e)}")
            raise


# 单例实例
_contract_reviewer = None


def get_contract_reviewer() -> ContractReviewer:
    """
    获取合同审查器实例
    """
    global _contract_reviewer
    if _contract_reviewer is None:
        _contract_reviewer = ContractReviewer()
    return _contract_reviewer
