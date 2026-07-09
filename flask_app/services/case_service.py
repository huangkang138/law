"""
案例服务类
"""

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from models.db_models import LegalCase, CaseExplanationSearch
from core.database import SessionLocal
from core.logger import app_logger


class CaseService:
    """
    案例服务类，处理案件搜索和管理
    """
    
    def search_similar_cases(self, query: str, use_web_search: bool = True) -> list:
        """
        搜索相似案件
        
        Args:
            query: 搜索关键词或案情描述
            use_web_search: 是否使用网络搜索获取真实案例
            
        Returns:
            相似案件列表
        """
        import re
        from services.web_search_service import WebSearchService
        
        def calculate_similarity(query_text: str, case: LegalCase) -> float:
            """
            计算查询文本与案例的相似度
            
            Args:
                query_text: 查询文本
                case: 案例对象
                
            Returns:
                相似度分数（0-100）
            """
            # 转换为小写进行比较
            query_lower = query_text.lower()
            title_lower = case.title.lower() if case.title else ""
            summary_lower = case.summary.lower() if case.summary else ""
            content_lower = case.content.lower() if case.content else ""
            
            # 计算匹配度
            score = 0
            
            # 标题匹配度（权重最高）
            if query_lower in title_lower:
                # 计算匹配比例
                match_ratio = len(query_lower) / len(title_lower)
                score += match_ratio * 40  # 最高40分
            
            # 摘要匹配度（权重次之）
            if query_lower in summary_lower:
                match_ratio = len(query_lower) / len(summary_lower)
                score += match_ratio * 30  # 最高30分
            
            # 内容匹配度（权重较低）
            if query_lower in content_lower:
                match_ratio = len(query_lower) / len(content_lower)
                score += match_ratio * 20  # 最高20分
            
            # 关键词匹配度（如果有）
            if case.keywords:
                keyword_match = False
                for keyword in case.keywords:
                    if query_lower in keyword.lower():
                        keyword_match = True
                        break
                if keyword_match:
                    score += 10  # 最高10分
            
            # 确保分数不超过100
            return min(100, score)
        
        db = SessionLocal()
        try:
            app_logger.info(f"搜索关键词: {query}, 使用网络搜索: {use_web_search}")
            
            results = []
            
            if use_web_search:
                # 使用网络搜索获取真实案例
                web_search_service = WebSearchService()
                web_results = web_search_service.search_legal_cases(query)
                results.extend(web_results)
                app_logger.info(f"网络搜索获取了 {len(web_results)} 个真实案例")
            
            # 获取本地数据库中的案例
            all_cases = db.query(LegalCase).all()
            
            # 计算每个案例的相似度
            cases_with_score = []
            for case in all_cases:
                similarity = calculate_similarity(query, case)
                if similarity > 0:  # 只保留有相似度的案例
                    cases_with_score.append((case, similarity))
            
            # 按相似度排序，取前10个
            cases_with_score.sort(key=lambda x: x[1], reverse=True)
            top_cases = cases_with_score[:10 - len(results)]  # 预留空间给网络搜索结果
            
            # 添加本地案例到结果
            for case, similarity in top_cases:
                results.append({
                    "id": case.id,
                    "title": case.title,
                    "case_number": case.case_number,
                    "court": case.court,
                    "date": case.date,
                    "summary": case.summary,
                    "similarity": round(similarity, 2),
                    "keywords": case.keywords or [],
                    "source": "本地数据库"
                })
            
            app_logger.info(f"找到 {len(results)} 个匹配的案件")
            for result in results:
                app_logger.info(f"匹配的案件: {result['title']} (相似度: {result['similarity']}%, 来源: {result.get('source', '本地')})")
            
            # 保存搜索记录
            search_record = CaseExplanationSearch(
                id=str(uuid.uuid4()),
                search_query=query,
                search_result=str(results),
                similar_cases=results
            )
            db.add(search_record)
            db.commit()
            db.refresh(search_record)
            
            app_logger.info(f"返回 {len(results)} 个搜索结果")
            return results, search_record.id
        except Exception as e:
            app_logger.error(f"搜索案件错误: {str(e)}")
            return [], str(uuid.uuid4())
        finally:
            db.close()
    
    def get_case_detail(self, case_id: str) -> dict:
        """
        获取案件详情
        
        Args:
            case_id: 案件ID
            
        Returns:
            案件详情
        """
        db = SessionLocal()
        try:
            case = db.query(LegalCase).filter(LegalCase.id == case_id).first()
            if not case:
                return None
            
            return {
                "id": case.id,
                "title": case.title,
                "case_number": case.case_number,
                "court": case.court,
                "date": case.date,
                "summary": case.summary,
                "content": case.content,
                "keywords": case.keywords or [],
                "case_type": case.case_type
            }
        except Exception as e:
            app_logger.error(f"获取案件详情失败: {str(e)}")
            return None
        finally:
            db.close()
    
    def get_search_history(self) -> list:
        """
        获取搜索历史
        
        Returns:
            搜索历史列表
        """
        db = SessionLocal()
        try:
            history = db.query(CaseExplanationSearch).order_by(
                CaseExplanationSearch.created_at.desc()
            ).limit(20).all()
            
            results = []
            for record in history:
                # 尝试解析相似案件数量
                result_count = 0
                try:
                    import json
                    if record.similar_cases:
                        result_count = len(record.similar_cases)
                except:
                    pass
                
                results.append({
                    "id": record.id,
                    "query": record.search_query[:100] + ("..." if len(record.search_query) > 100 else ""),
                    "timestamp": record.created_at.strftime("%Y-%m-%d %H:%M"),
                    "result_count": result_count
                })
            
            return results
        except Exception as e:
            app_logger.error(f"获取搜索历史失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def delete_search_history(self, search_id: str) -> bool:
        """
        删除搜索历史记录
        
        Args:
            search_id: 搜索历史记录ID
            
        Returns:
            是否删除成功
        """
        db = SessionLocal()
        try:
            record = db.query(CaseExplanationSearch).filter(
                CaseExplanationSearch.id == search_id
            ).first()
            
            if record:
                db.delete(record)
                db.commit()
                return True
            return False
        except Exception as e:
            app_logger.error(f"删除搜索历史失败: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_search_history_detail(self, search_id: str) -> dict:
        """
        获取单个搜索历史记录详情
        
        Args:
            search_id: 搜索历史记录ID
            
        Returns:
            搜索历史记录详情
        """
        db = SessionLocal()
        try:
            record = db.query(CaseExplanationSearch).filter(
                CaseExplanationSearch.id == search_id
            ).first()
            
            if not record:
                return None
            
            return {
                "id": record.id,
                "query": record.search_query,
                "timestamp": record.created_at.strftime("%Y-%m-%d %H:%M"),
                "similar_cases": record.similar_cases or []
            }
        except Exception as e:
            app_logger.error(f"获取搜索历史详情失败: {str(e)}")
            return None
        finally:
            db.close()
    
    def create_case(self, case_data: dict) -> LegalCase:
        """
        创建新案例
        
        Args:
            case_data: 案例数据
            
        Returns:
            创建的案例对象
        """
        db = SessionLocal()
        try:
            case = LegalCase(
                id=str(uuid.uuid4()),
                title=case_data.get('title'),
                case_number=case_data.get('case_number'),
                court=case_data.get('court'),
                date=case_data.get('date'),
                summary=case_data.get('summary'),
                content=case_data.get('content'),
                keywords=case_data.get('keywords', []),
                case_type=case_data.get('case_type', '民事')
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            return case
        except Exception as e:
            app_logger.error(f"创建案例失败: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()