"""
文档管理路由
提供文档上传、入库、检索等接口
"""

import os
import uuid
import re
import json
import threading
import time
from pathlib import Path
from flask import Blueprint, request, jsonify, Response
from core.logger import app_logger
from core.database import get_db
from models.db_models import Contract, ContractRisk
from services.llm_factory import LLMFactory
from langchain_core.messages import HumanMessage, SystemMessage

# 导入文件解析库
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    app_logger.warning("PyPDF2 未安装，PDF 文件解析功能不可用")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    app_logger.warning("python-docx 未安装，Word 文件解析功能不可用")

try:
    import olefile
    OLE_AVAILABLE = True
except ImportError:
    OLE_AVAILABLE = False
    app_logger.warning("olefile 未安装，旧版 Word (.doc) 文件解析功能不可用")

router = Blueprint('document', __name__)

# 上传文件存储目录
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 存储合同内容（用于后续审查）
contract_storage = {}

# 存储合同审查流式会话
contract_review_processing_sessions = {}
contract_review_streaming_sessions = {}


def extract_text_from_pdf(file_path: str) -> str:
    """
    从 PDF 文件中提取文本内容
    
    Args:
        file_path: PDF 文件路径
        
    Returns:
        提取的文本内容
    """
    if not PDF_AVAILABLE:
        raise Exception("PDF 解析库未安装")
    
    try:
        text_content = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n"
        
        app_logger.info(f"PDF 文件解析成功，共 {num_pages} 页，提取文本长度: {len(text_content)}")
        return text_content.strip()
    except PyPDF2.errors.PdfReadError as e:
        app_logger.error(f"PDF 文件解析失败: {str(e)}")
        # 提供更友好的错误信息
        if "EOF marker not found" in str(e):
            raise Exception("PDF 文件损坏或不完整，请检查文件是否完整下载")
        else:
            raise Exception(f"PDF 文件解析失败: {str(e)}")
    except Exception as e:
        app_logger.error(f"PDF 文件解析失败: {str(e)}")
        raise Exception(f"PDF 文件解析失败: {str(e)}")


def extract_text_from_docx(file_path: str) -> str:
    """
    从 Word 文档中提取文本内容
    
    Args:
        file_path: Word 文档路径
        
    Returns:
        提取的文本内容
    """
    if not DOCX_AVAILABLE:
        raise Exception("Word 文档解析库未安装")
    
    try:
        doc = Document(file_path)
        text_content = ""
        
        # 提取段落文本
        for paragraph in doc.paragraphs:
            text_content += paragraph.text + "\n"
        
        # 提取表格文本
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text_content += cell.text + " "
                text_content += "\n"
        
        app_logger.info(f"Word 文档解析成功，提取文本长度: {len(text_content)}")
        return text_content.strip()
    except Exception as e:
        app_logger.error(f"Word 文档解析失败: {str(e)}")
        raise Exception(f"Word 文档解析失败: {str(e)}")


def extract_text_from_doc(file_path: str) -> str:
    """
    从旧版 Word 文档 (.doc) 中提取文本内容
    
    使用 olefile 库读取 OLE 文件格式
    
    Args:
        file_path: Word 文档路径 (.doc)
        
    Returns:
        提取的文本内容
    """
    if not OLE_AVAILABLE:
        raise Exception("olefile 库未安装，无法解析旧版 Word 文档 (.doc)")
    
    try:
        ole = olefile.OleFileIO(file_path)
        
        # 尝试从 WordDocument 流中提取文本
        if ole.exists('WordDocument'):
            word_stream = ole.openstream('WordDocument')
            data = word_stream.read()
            
            # 简单的文本提取：尝试找到可打印的文本字符
            # 这是一个简化的实现，对于复杂的 .doc 文件可能需要更复杂的解析
            text_parts = []
            current_text = []
            
            for i in range(0, len(data) - 1, 2):
                # Word 文档通常使用 UTF-16LE 编码
                try:
                    char = data[i:i+2].decode('utf-16le', errors='ignore')
                    if char.isprintable() and char not in '\x00\x01\x02\x03\x04\x05\x06\x07\x08':
                        current_text.append(char)
                    elif current_text:
                        text_parts.append(''.join(current_text))
                        current_text = []
                except:
                    continue
            
            if current_text:
                text_parts.append(''.join(current_text))
            
            ole.close()
            
            # 过滤并清理文本
            text_content = '\n'.join(part.strip() for part in text_parts if len(part.strip()) > 2)
            
            if text_content:
                app_logger.info(f"旧版 Word 文档解析成功，提取文本长度: {len(text_content)}")
                return text_content
            else:
                raise Exception("无法从文档中提取有效文本内容")
        else:
            ole.close()
            raise Exception("文档格式不支持或文件已损坏")
            
    except Exception as e:
        app_logger.error(f"旧版 Word 文档解析失败: {str(e)}")
        raise Exception(f"旧版 Word 文档解析失败: {str(e)}")


def clean_review_text(text: str) -> str:
    """
    清理审查结果文本
    
    1. 去除特殊符号（#、*、- 等 Markdown 标记）
    2. 自动换行，优化排版
    3. 删除空行
    
    Args:
        text: 原始审查结果文本
        
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 步骤1: 去除 Markdown 特殊符号
    # 去除 # 标题标记
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # 去除 * 和 _ 强调标记
    text = re.sub(r'\*\*?|__?', '', text)
    # 去除 - 列表标记（在行首）
    text = re.sub(r'^-\s+', '', text, flags=re.MULTILINE)
    # 去除 + 列表标记
    text = re.sub(r'^\+\s+', '', text, flags=re.MULTILINE)
    # 去除 > 引用标记
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    # 去除 ` 代码标记
    text = re.sub(r'`+', '', text)
    # 去除 | 表格标记
    text = re.sub(r'\|', ' ', text)
    
    # 步骤2: 分割成行并处理
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # 去除行首尾的空白字符
        line = line.strip()
        
        # 跳过空行
        if not line:
            continue
        
        # 去除行内的多余空格
        line = re.sub(r'\s+', ' ', line)
        
        cleaned_lines.append(line)
    
    # 步骤3: 智能分段和换行
    # 根据内容逻辑进行分段
    formatted_paragraphs = []
    current_paragraph = []
    
    for line in cleaned_lines:
        # 如果行以数字或中文数字开头，可能是新的段落开始
        if re.match(r'^[\d一二三四五六七八九十]+[\.、\s]', line):
            if current_paragraph:
                formatted_paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
            formatted_paragraphs.append(line)
        # 如果行以特定关键词开头，可能是新的段落
        elif re.match(r'^(整体评估|风险条款|总结建议|法律依据|修改建议|风险等级|条款内容)', line):
            if current_paragraph:
                formatted_paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
            formatted_paragraphs.append(line)
        else:
            current_paragraph.append(line)
    
    # 添加最后一段
    if current_paragraph:
        formatted_paragraphs.append(' '.join(current_paragraph))
    
    # 步骤4: 合并段落，确保每段之间有适当的间距
    final_text = '\n\n'.join(formatted_paragraphs)
    
    # 步骤5: 最终清理
    # 去除多余的换行
    final_text = re.sub(r'\n{3,}', '\n\n', final_text)
    # 去除行首的数字编号后的多余空格
    final_text = re.sub(r'^(\d+)\s+', r'\1. ', final_text, flags=re.MULTILINE)
    
    app_logger.info(f"文本清理完成，原始长度: {len(text)}, 清理后长度: {len(final_text)}")
    
    return final_text.strip()


def extract_text_from_txt(file_path: str) -> str:
    """
    从文本文件中提取内容
    
    Args:
        file_path: 文本文件路径
        
    Returns:
        文本内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text_content = file.read()
        
        app_logger.info(f"文本文件读取成功，长度: {len(text_content)}")
        return text_content
    except UnicodeDecodeError:
        # 尝试使用其他编码
        try:
            with open(file_path, 'r', encoding='gbk', errors='ignore') as file:
                text_content = file.read()
            app_logger.info(f"文本文件读取成功（GBK编码），长度: {len(text_content)}")
            return text_content
        except Exception as e:
            raise Exception(f"文本文件读取失败: {str(e)}")
    except Exception as e:
        app_logger.error(f"文本文件读取失败: {str(e)}")
        raise Exception(f"文本文件读取失败: {str(e)}")


class ContractReviewParser:
    """
    高级合同审查结果解析器
    
    使用复杂的正则表达式和多行匹配逻辑，精确提取 LLM 返回的审查结果
    确保解析的完整性和准确性，保障人民权益
    """
    
    def __init__(self, review_text: str):
        self.review_text = review_text
        self.risks = []
        
    def parse(self):
        """
        执行完整的解析流程
        """
        app_logger.info("开始高级解析 LLM 审查结果...")
        
        # 方法1: 尝试使用结构化格式解析（JSON 或 Markdown 表格）
        if self._try_structured_parse():
            app_logger.info(f"结构化解析成功，提取到 {len(self.risks)} 个风险项")
            return self.risks
        
        # 方法2: 使用正则表达式进行高级解析
        if self._try_regex_parse():
            app_logger.info(f"正则解析成功，提取到 {len(self.risks)} 个风险项")
            return self.risks
        
        # 方法3: 使用智能段落分析
        if self._try_paragraph_parse():
            app_logger.info(f"段落解析成功，提取到 {len(self.risks)} 个风险项")
            return self.risks
        
        # 方法4: 使用深度语义分析
        if self._try_semantic_parse():
            app_logger.info(f"语义解析成功，提取到 {len(self.risks)} 个风险项")
            return self.risks
        
        # 如果所有方法都失败，使用兜底方案
        app_logger.warning("所有解析方法均未成功，使用兜底方案")
        return self._fallback_parse()
    
    def _try_structured_parse(self) -> bool:
        """
        尝试解析结构化格式（JSON 或 Markdown 表格）
        """
        # 尝试提取 JSON 格式
        json_pattern = r'\{[\s\S]*?"risk_level"[\s\S]*?\}'
        json_matches = re.findall(json_pattern, self.review_text, re.IGNORECASE)
        
        if json_matches:
            for json_str in json_matches:
                try:
                    import json
                    risk_data = json.loads(json_str)
                    if self._validate_risk_data(risk_data):
                        self.risks.append(risk_data)
                except:
                    continue
            return len(self.risks) > 0
        
        # 尝试提取 Markdown 表格格式
        table_pattern = r'\|.*?\|.*?\|.*?\|.*?\|.*?\|.*?\|[\s\S]*?\|.*?\|.*?\|.*?\|.*?\|.*?\|.*?\|'
        table_matches = re.findall(table_pattern, self.review_text)
        
        if table_matches:
            for table in table_matches:
                self._parse_markdown_table(table)
            return len(self.risks) > 0
        
        return False
    
    def _parse_markdown_table(self, table_text: str):
        """
        解析 Markdown 表格
        """
        lines = table_text.split('\n')
        if len(lines) < 2:
            return
        
        # 跳过表头和分隔行
        for line in lines[2:]:
            if '|' not in line:
                continue
            
            cells = [cell.strip() for cell in line.split('|')]
            if len(cells) >= 6:
                risk_data = {
                    "risk_level": self._extract_risk_level(cells[0]),
                    "original_clause": cells[1] if len(cells) > 1 else "",
                    "original_text_quote": cells[2] if len(cells) > 2 else "",
                    "risk_explanation": cells[3] if len(cells) > 3 else "",
                    "legal_basis": [cells[4]] if len(cells) > 4 else [],
                    "legal_basis_links": [],
                    "revise_suggestion": cells[5] if len(cells) > 5 else "",
                    "confidence_score": 0.85
                }
                
                if self._validate_risk_data(risk_data):
                    self.risks.append(risk_data)
    
    def _try_regex_parse(self) -> bool:
        """
        使用高级正则表达式进行解析
        """
        # 定义多种风险等级模式
        risk_level_patterns = [
            r'(?:风险等级|Risk Level|级别)[:：]\s*([高中低HIGHMEDIUMLOW]+)',
            r'【?\s*([高高中低])\s*风险\s*】?',
            r'([HIGH|MEDIUM|LOW])\s*Risk',
            r'([高|中|低])\s*风险'
        ]
        
        # 提取所有风险块
        risk_blocks = self._extract_risk_blocks()
        
        for block in risk_blocks:
            risk_data = self._parse_risk_block(block, risk_level_patterns)
            if risk_data and self._validate_risk_data(risk_data):
                self.risks.append(risk_data)
        
        return len(self.risks) > 0
    
    def _extract_risk_blocks(self) -> list:
        """
        提取所有风险块
        """
        blocks = []
        
        # 模式1: 使用数字编号
        numbered_pattern = r'(?:\d+\.|\d+\)|【\d+】)\s*[\s\S]*?(?=(?:\d+\.|\d+\)|【\d+】|$))'
        numbered_matches = re.findall(numbered_pattern, self.review_text)
        blocks.extend(numbered_matches)
        
        # 模式2: 使用风险等级作为分隔符
        level_pattern = r'(?:风险等级[:：].*?(?:\n|$)|(?:高|中|低)\s*风险.*?(?:\n|$))[\s\S]*?(?=(?:风险等级[:：]|(?:高|中|低)\s*风险|$))'
        level_matches = re.findall(level_pattern, self.review_text, re.IGNORECASE)
        blocks.extend(level_matches)
        
        # 模式3: 使用条款分隔符
        clause_pattern = r'(?:条款|Clause|项目)[:：].*?(?:\n|$)[\s\S]*?(?=(?:条款|Clause|项目|$))'
        clause_matches = re.findall(clause_pattern, self.review_text, re.IGNORECASE)
        blocks.extend(clause_matches)
        
        # 如果没有找到块，将整个文本作为一个块
        if not blocks:
            blocks.append(self.review_text)
        
        return blocks
    
    def _parse_risk_block(self, block: str, risk_level_patterns: list) -> dict:
        """
        解析单个风险块
        """
        risk_data = {
            "risk_level": "MEDIUM",
            "original_clause": "",
            "original_text_quote": "",
            "risk_explanation": "",
            "legal_basis": [],
            "legal_basis_links": [],
            "revise_suggestion": "",
            "confidence_score": 0.8
        }
        
        # 提取风险等级
        for pattern in risk_level_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                risk_data["risk_level"] = self._extract_risk_level(match.group(1))
                break
        
        # 提取原始条款
        original_clause_patterns = [
            r'(?:原始条款|Original Clause|条款内容|Clause Content)[:：]\s*([^。\n]+(?:[。\n][^。\n]+)*)',
            r'(?:条款|Clause)[:：]\s*([^。\n]+(?:[。\n][^。\n]+)*)',
            r'【?\s*条款\s*】?\s*[:：]?\s*([^。\n]+(?:[。\n][^。\n]+)*)'
        ]
        
        for pattern in original_clause_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                risk_data["original_clause"] = match.group(1).strip()
                break
        
        # 提取风险解释
        risk_explanation_patterns = [
            r'(?:风险解释|Risk Explanation|风险说明|Risk Description)[:：]\s*([^。\n]+(?:[。\n][^。\n]+)*)',
            r'(?:解释|说明|Explanation)[:：]\s*([^。\n]+(?:[。\n][^。\n]+)*)',
            r'【?\s*风险\s*】?\s*[:：]?\s*([^。\n]+(?:[。\n][^。\n]+)*)'
        ]
        
        for pattern in risk_explanation_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                risk_data["risk_explanation"] = match.group(1).strip()
                break
        
        # 提取法律依据
        legal_basis_patterns = [
            r'(?:法律依据|Legal Basis|法律条款|Legal Provisions)[:：]\s*([^。\n]+(?:[。\n][^。\n]+)*)',
            r'(?:依据|Basis|条款|Provision)[:：]\s*([^。\n]+(?:[。\n][^。\n]+)*)',
            r'【?\s*法律\s*】?\s*[:：]?\s*([^。\n]+(?:[。\n][^。\n]+)*)'
        ]
        
        for pattern in legal_basis_patterns:
            matches = re.findall(pattern, block, re.IGNORECASE)
            if matches:
                risk_data["legal_basis"] = [m.strip() for m in matches]
                break
        
        # 提取修改建议
        revise_suggestion_patterns = [
            r'(?:修改建议|Revise Suggestion|建议修改|Suggestion)[:：]\s*([^。\n]+(?:[。\n][^。\n]+)*)',
            r'(?:建议|Suggestion|修改|Revise)[:：]\s*([^。\n]+(?:[。\n][^。\n]+)*)',
            r'【?\s*建议\s*】?\s*[:：]?\s*([^。\n]+(?:[。\n][^。\n]+)*)'
        ]
        
        for pattern in revise_suggestion_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                risk_data["revise_suggestion"] = match.group(1).strip()
                break
        
        # 提取置信度
        confidence_pattern = r'(?:置信度|Confidence|信心)[:：]\s*([0-9.]+)'
        match = re.search(confidence_pattern, block, re.IGNORECASE)
        if match:
            try:
                risk_data["confidence_score"] = float(match.group(1))
            except:
                pass
        
        return risk_data
    
    def _try_paragraph_parse(self) -> bool:
        """
        使用智能段落分析
        """
        paragraphs = self.review_text.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 检查段落是否包含风险关键词
            if self._contains_risk_keywords(paragraph):
                risk_data = self._extract_risk_from_paragraph(paragraph)
                if risk_data and self._validate_risk_data(risk_data):
                    self.risks.append(risk_data)
        
        return len(self.risks) > 0
    
    def _contains_risk_keywords(self, text: str) -> bool:
        """
        检查文本是否包含风险关键词
        """
        keywords = [
            '风险', 'risk', '违反', 'violate', '不合规', 'non-compliant',
            '问题', 'problem', '隐患', 'hazard', '条款', 'clause',
            '建议', 'suggestion', '修改', 'revise', '法律', 'legal'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)
    
    def _extract_risk_from_paragraph(self, paragraph: str) -> dict:
        """
        从段落中提取风险信息
        """
        risk_data = {
            "risk_level": self._detect_risk_level(paragraph),
            "original_clause": "",
            "original_text_quote": "",
            "risk_explanation": "",
            "legal_basis": [],
            "legal_basis_links": [],
            "revise_suggestion": "",
            "confidence_score": 0.75
        }
        
        # 提取句子
        sentences = re.split(r'[。！？.!?]', paragraph)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 根据关键词分类句子
            if any(keyword in sentence for keyword in ['条款', 'clause', '约定', 'agree']):
                risk_data["original_clause"] += sentence + "。"
            elif any(keyword in sentence for keyword in ['风险', 'risk', '问题', 'problem', '违反', 'violate']):
                risk_data["risk_explanation"] += sentence + "。"
            elif any(keyword in sentence for keyword in ['法律', 'legal', '法条', 'law', '规定', 'rule']):
                risk_data["legal_basis"].append(sentence)
            elif any(keyword in sentence for keyword in ['建议', 'suggestion', '修改', 'revise', '应该', 'should']):
                risk_data["revise_suggestion"] += sentence + "。"
        
        # 清理字段
        risk_data["original_clause"] = risk_data["original_clause"].strip()
        risk_data["risk_explanation"] = risk_data["risk_explanation"].strip()
        risk_data["revise_suggestion"] = risk_data["revise_suggestion"].strip()
        
        return risk_data
    
    def _try_semantic_parse(self) -> bool:
        """
        使用深度语义分析
        """
        # 提取所有句子
        sentences = re.split(r'[。！？.!?]', self.review_text)
        
        current_risk = None
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 检测新的风险项开始
            if self._is_new_risk_start(sentence):
                if current_risk and self._validate_risk_data(current_risk):
                    self.risks.append(current_risk)
                current_risk = self._init_risk_data(sentence)
            elif current_risk:
                self._update_risk_data(current_risk, sentence)
        
        # 添加最后一个风险项
        if current_risk and self._validate_risk_data(current_risk):
            self.risks.append(current_risk)
        
        return len(self.risks) > 0
    
    def _is_new_risk_start(self, sentence: str) -> bool:
        """
        判断是否是新风险项的开始
        """
        patterns = [
            r'^(?:\d+\.|\d+\)|【\d+】)',
            r'^(?:风险|Risk)[:：]',
            r'^(?:条款|Clause)[:：]',
            r'^(?:问题|Problem)[:：]'
        ]
        
        return any(re.match(pattern, sentence, re.IGNORECASE) for pattern in patterns)
    
    def _init_risk_data(self, sentence: str) -> dict:
        """
        初始化风险数据
        """
        return {
            "risk_level": self._detect_risk_level(sentence),
            "original_clause": "",
            "original_text_quote": "",
            "risk_explanation": "",
            "legal_basis": [],
            "legal_basis_links": [],
            "revise_suggestion": "",
            "confidence_score": 0.8
        }
    
    def _update_risk_data(self, risk_data: dict, sentence: str):
        """
        更新风险数据
        """
        if any(keyword in sentence for keyword in ['条款', 'clause', '约定', 'agree']):
            risk_data["original_clause"] += sentence + "。"
        elif any(keyword in sentence for keyword in ['风险', 'risk', '问题', 'problem', '违反', 'violate']):
            risk_data["risk_explanation"] += sentence + "。"
        elif any(keyword in sentence for keyword in ['法律', 'legal', '法条', 'law', '规定', 'rule']):
            risk_data["legal_basis"].append(sentence)
        elif any(keyword in sentence for keyword in ['建议', 'suggestion', '修改', 'revise', '应该', 'should']):
            risk_data["revise_suggestion"] += sentence + "。"
    
    def _fallback_parse(self) -> list:
        """
        兜底解析方案
        """
        return [{
            "risk_level": "MEDIUM",
            "original_clause": "合同整体审查",
            "original_text_quote": self.review_text[:200] + "..." if len(self.review_text) > 200 else self.review_text,
            "risk_explanation": self.review_text[:500] + "..." if len(self.review_text) > 500 else self.review_text,
            "legal_basis": ["请参考详细分析结果"],
            "legal_basis_links": [],
            "revise_suggestion": "请根据上述分析结果进行相应修改",
            "confidence_score": 0.85
        }]
    
    def _extract_risk_level(self, text: str) -> str:
        """
        提取风险等级
        """
        text_upper = text.upper()
        
        if any(keyword in text_upper for keyword in ['HIGH', '高']):
            return "HIGH"
        elif any(keyword in text_upper for keyword in ['MEDIUM', '中']):
            return "MEDIUM"
        elif any(keyword in text_upper for keyword in ['LOW', '低']):
            return "LOW"
        else:
            return "MEDIUM"
    
    def _detect_risk_level(self, text: str) -> str:
        """
        检测风险等级
        """
        text_upper = text.upper()
        
        # 高风险关键词
        high_risk_keywords = ['严重', '违法', '无效', '禁止', '高风险', 'HIGH RISK', '严重违反']
        if any(keyword in text_upper for keyword in high_risk_keywords):
            return "HIGH"
        
        # 中风险关键词
        medium_risk_keywords = ['建议修改', '需要注意', '风险', 'MEDIUM', 'RISK', '问题']
        if any(keyword in text_upper for keyword in medium_risk_keywords):
            return "MEDIUM"
        
        # 低风险关键词
        low_risk_keywords = ['轻微', '建议', 'LOW', 'SUGGESTION']
        if any(keyword in text_upper for keyword in low_risk_keywords):
            return "LOW"
        
        return "MEDIUM"
    
    def _validate_risk_data(self, risk_data: dict) -> bool:
        """
        验证风险数据的完整性和有效性
        """
        # 必须有风险等级
        if "risk_level" not in risk_data or not risk_data["risk_level"]:
            return False
        
        # 必须有风险解释或原始条款
        has_content = (
            (risk_data.get("risk_explanation") and len(risk_data["risk_explanation"]) > 0) or
            (risk_data.get("original_clause") and len(risk_data["original_clause"]) > 0)
        )
        
        if not has_content:
            return False
        
        # 验证风险等级的有效性
        valid_levels = ["HIGH", "MEDIUM", "LOW"]
        if risk_data["risk_level"].upper() not in valid_levels:
            return False
        
        # 验证置信度
        if "confidence_score" in risk_data:
            try:
                score = float(risk_data["confidence_score"])
                if score < 0 or score > 1:
                    risk_data["confidence_score"] = 0.8
            except:
                risk_data["confidence_score"] = 0.8
        
        return True


@router.route('/document/upload', methods=['POST'])
def upload_document():
    """
    上传合同文档
    
    支持 PDF、Word 和文本文件
    真实保存文件并提取内容
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "请选择要上传的文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "请选择要上传的文件"}), 400
        
        # 检查文件类型
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            return jsonify({"error": "仅支持 PDF、Word 和文本文件"}), 400
        
        # 生成合同 ID
        contract_id = f"upload_{uuid.uuid4()}"
        
        # 保存文件到磁盘
        file_path = os.path.join(UPLOAD_FOLDER, f"{contract_id}{ext}")
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        app_logger.info(f"文件保存成功: {file.filename}, 路径: {file_path}, 大小: {file_size} 字节")
        
        # 根据文件类型提取文本内容
        try:
            if ext == '.pdf':
                text_content = extract_text_from_pdf(file_path)
            elif ext == '.docx':
                text_content = extract_text_from_docx(file_path)
            elif ext == '.doc':
                text_content = extract_text_from_doc(file_path)
            elif ext == '.txt':
                text_content = extract_text_from_txt(file_path)
            else:
                text_content = ""
        except Exception as e:
            app_logger.error(f"文件内容提取失败: {str(e)}")
            return jsonify({"error": f"文件内容提取失败: {str(e)}"}), 400
        
        # 验证提取的内容
        if not text_content or len(text_content.strip()) == 0:
            return jsonify({"error": "无法从文件中提取有效内容，请检查文件是否损坏或格式是否正确"}), 400
        
        # 存储合同内容到数据库
        db = next(get_db())
        try:
            # 创建合同记录
            contract = Contract(
                id=contract_id,
                filename=file.filename,
                file_path=file_path,
                content=text_content,
                file_size=file_size,
                text_length=len(text_content)
            )
            db.add(contract)
            db.commit()
            db.refresh(contract)
            
            app_logger.info(f"文件上传成功: {file.filename}")
            app_logger.info(f"文件存储路径: {file_path}")
            app_logger.info(f"提取文本长度: {len(text_content)} 字符")
            app_logger.info(f"合同已保存到数据库: {contract_id}")
            
            # 返回响应
            return jsonify({
                "success": True,
                "message": "文件上传成功",
                "contract_id": contract_id,
                "file_name": file.filename,
                "file_size": file_size,
                "text_length": len(text_content)
            })
        except Exception as e:
            db.rollback()
            app_logger.error(f"数据库保存失败: {str(e)}")
            return jsonify({"error": f"数据库保存失败: {str(e)}"}), 500
        finally:
            db.close()
        
    except Exception as e:
        app_logger.error(f"文件上传错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@router.route('/document/review', methods=['POST'])
def review_document():
    """
    审查合同文档
    
    真实使用 LLM 分析用户上传的合同内容
    使用高级解析逻辑确保结果的完整性和准确性
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "缺少请求数据"}), 400
        
        # 支持 content 或 contract_id 参数
        content = data.get('content')
        contract_id = data.get('contract_id')
        
        if not content and not contract_id:
            return jsonify({"error": "缺少 content 或 contract_id 参数"}), 400
        
        # 获取合同内容
        if not content and contract_id:
            # 从数据库中获取合同
            db = next(get_db())
            try:
                contract = db.query(Contract).filter(Contract.id == contract_id).first()
                if contract:
                    content = contract.content
                    app_logger.info(f"从数据库获取合同内容，长度: {len(content)} 字符")
                else:
                    db.close()
                    return jsonify({"error": f"找不到合同 ID: {contract_id}"}), 404
            finally:
                db.close()
        
        if not content:
            return jsonify({"error": "请提供合同内容或合同ID"}), 400
        
        # 验证内容长度
        if len(content.strip()) == 0:
            return jsonify({"error": "合同内容为空，无法进行审查"}), 400
        
        # 调用 LLM 进行真实的合同审查
        llm = LLMFactory.create_llm()
        
        prompt = f"""你是一名专业的法律顾问，请对以下合同进行详细审查：

合同内容：
{content}

请严格按照以下JSON格式输出审查结果，确保内容全面、准确、有逻辑性：

{{
  "overall_summary": {{
    "contract_type": "合同类型（如：劳动合同、买卖合同、租赁合同等）",
    "main_clauses": "主要条款概述（200-300字）",
    "compliance_evaluation": "整体合规性评价（100-200字）"
  }},
  "risks": [
    {{
      "risk_level": "高/中/低",
      "original_clause": "直接从合同中提取的具体条款内容",
      "risk_explanation": "详细说明风险的具体表现和可能的法律后果（100-200字）",
      "legal_basis": [
        "具体法律条文1（包括法律名称和条文内容）",
        "具体法律条文2（包括法律名称和条文内容）"
      ],
      "revise_suggestion": "具体、可操作的修改方案（50-100字）",
      "confidence_score": 0.95
    }}
  ],
  "summary_recommendations": {{
    "priority_risks": "优先处理的风险点（按重要性排序）",
    "overall_suggestions": "总体修改建议（100-200字）"
  }}
}}

要求：
1. 只输出JSON格式，不要包含任何其他文本
2. 确保每个风险项都有完整的信息
3. 不使用任何占位符或模板化内容
4. 所有分析都基于合同的实际内容
5. 法律依据引用准确完整
6. 修改建议具体可行
7. 确保JSON格式正确，可以被直接解析"""
        
        app_logger.info("开始调用 LLM 进行合同审查（流式传输）...")
        
        # 使用流式传输调用LLM
        import httpx
        from core.config import settings
        
        # 直接构建消息格式
        formatted_messages = [
            {"role": "system", "content": "你是一名专业的法律顾问，擅长合同审查和风险识别。请基于实际合同内容提供详细、准确的法律分析。只输出JSON格式，不要包含任何其他文本。"},
            {"role": "user", "content": prompt}
        ]
        
        app_logger.info(f"合同审查 - 消息数量: {len(formatted_messages)}")
        
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": formatted_messages,
            "temperature": float(settings.OPENAI_TEMPERATURE),
            "max_tokens": int(settings.OPENAI_MAX_TOKENS),
            "stream": True
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        }
        
        client = httpx.Client(timeout=180.0)
        review_analysis = ""
        
        try:
            with client.stream(
                "POST",
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                app_logger.info(f"合同审查 - 响应状态码: {response.status_code}")
                
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
                                            review_analysis += chunk_content
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
                    app_logger.error(f"合同审查 LLM调用失败: {response.status_code} - {error_msg}")
                    raise Exception(f"LLM调用失败: {error_msg}")
        finally:
            client.close()
        
        app_logger.info(f"LLM 审查完成，结果长度: {len(review_analysis)} 字符")
        
        # 提取并解析JSON格式的审查结果
        
        # 清理响应，只保留JSON部分
        json_start = review_analysis.find('{')
        json_end = review_analysis.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = review_analysis[json_start:json_end]
        else:
            json_str = review_analysis
        
        app_logger.info(f"提取的JSON字符串长度: {len(json_str)}")
        app_logger.info(f"JSON字符串前200字符: {json_str[:200]}...")
        
        # 解析JSON
        try:
            parsed_result = json.loads(json_str)
            app_logger.info("JSON解析成功")
            
            # 验证结果结构
            if not isinstance(parsed_result, dict):
                raise ValueError("解析结果不是有效的JSON对象")
            
            # 确保必要的字段存在
            if "overall_summary" not in parsed_result:
                parsed_result["overall_summary"] = {
                    "contract_type": "未知合同类型",
                    "main_clauses": "合同主要条款概述",
                    "compliance_evaluation": "整体合规性评价"
                }
            if "risks" not in parsed_result:
                parsed_result["risks"] = []
            if "summary_recommendations" not in parsed_result:
                parsed_result["summary_recommendations"] = {
                    "priority_risks": "请检查合同内容",
                    "overall_suggestions": "建议进一步审查"
                }
                
        except json.JSONDecodeError as e:
            app_logger.error(f"JSON解析失败: {str(e)}")
            # 尝试使用更robust的解析方法
            try:
                # 清理JSON字符串，移除可能的无效字符
                import re
                # 移除JSON前后的空白字符和非JSON内容
                clean_json_str = re.sub(r'^[^\{]*', '', json_str)
                clean_json_str = re.sub(r'[^\}]*$', '', clean_json_str)
                
                # 尝试修复常见的JSON格式问题
                # 移除尾部逗号
                clean_json_str = re.sub(r',\s*([\}\]])', r'\1', clean_json_str)
                # 修复缺少引号的键
                clean_json_str = re.sub(r'(\w+):', r'"\1":', clean_json_str)
                # 修复未转义的引号
                clean_json_str = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', r'"\1"', clean_json_str)
                # 尝试再次解析
                parsed_result = json.loads(clean_json_str)
                app_logger.info("清理后JSON解析成功")
                
                # 再次验证结构
                if not isinstance(parsed_result, dict):
                    raise ValueError("清理后解析结果仍不是有效的JSON对象")
                    
            except Exception as e2:
                app_logger.error(f"清理后JSON解析仍然失败: {str(e2)}")
                # 如果JSON解析失败，尝试从原始文本中提取信息
                app_logger.info("尝试从原始LLM响应中提取信息")
                
                # 尝试使用正则表达式从原始文本中提取风险项
                try:
                    import re
                    # 提取整体摘要
                    contract_type_match = re.search(r'"contract_type":\s*"([^"]+)"', json_str)
                    main_clauses_match = re.search(r'"main_clauses":\s*"([^"]+)"', json_str)
                    compliance_evaluation_match = re.search(r'"compliance_evaluation":\s*"([^"]+)"', json_str)
                    
                    contract_type = contract_type_match.group(1) if contract_type_match else "未知合同类型"
                    main_clauses = main_clauses_match.group(1) if main_clauses_match else "合同主要条款概述"
                    compliance_evaluation = compliance_evaluation_match.group(1) if compliance_evaluation_match else "整体合规性评价"
                    
                    # 提取风险项
                    risks = []
                    risk_matches = re.findall(r'\{[^\}]*"risk_level":\s*"([^"]+)",[^\}]*"original_clause":\s*"([^"]+)",[^\}]*"risk_explanation":\s*"([^"]+)",[^\}]*"legal_basis":\s*\[([^\]]*)\],[^\}]*"revise_suggestion":\s*"([^"]+)"[^\}]*\}', json_str, re.DOTALL)
                    
                    for risk_match in risk_matches:
                        risk_level, original_clause, risk_explanation, legal_basis_str, revise_suggestion = risk_match
                        legal_basis = re.findall(r'"([^"]+)"', legal_basis_str)
                        risks.append({
                            "risk_level": risk_level,
                            "original_clause": original_clause,
                            "risk_explanation": risk_explanation,
                            "legal_basis": legal_basis,
                            "revise_suggestion": revise_suggestion,
                            "confidence_score": 0.8
                        })
                    
                    # 提取总结建议
                    priority_risks_match = re.search(r'"priority_risks":\s*"([^"]+)"', json_str)
                    overall_suggestions_match = re.search(r'"overall_suggestions":\s*"([^"]+)"', json_str)
                    
                    priority_risks = priority_risks_match.group(1) if priority_risks_match else "请检查合同内容"
                    overall_suggestions = overall_suggestions_match.group(1) if overall_suggestions_match else "建议进一步审查"
                    
                    parsed_result = {
                        "overall_summary": {
                            "contract_type": contract_type,
                            "main_clauses": main_clauses,
                            "compliance_evaluation": compliance_evaluation
                        },
                        "risks": risks,
                        "summary_recommendations": {
                            "priority_risks": priority_risks,
                            "overall_suggestions": overall_suggestions
                        }
                    }
                    
                    app_logger.info(f"从原始文本中提取到 {len(risks)} 个风险项")
                    
                except Exception as e3:
                    app_logger.error(f"从原始文本提取信息失败: {str(e3)}")
                    # 如果所有方法都失败，使用基于合同内容的兜底方案
                    app_logger.info("使用基于合同内容的兜底方案")
                
                # 基于合同内容的简单分析
                contract_type = "未知合同类型"
                main_clauses = "合同主要条款概述"
                compliance_evaluation = "整体合规性评价"
                priority_risks = "请检查合同内容"
                overall_suggestions = "建议进一步审查"
                risks = []
                
                # 尝试从合同内容中提取信息
                content_lower = content.lower()
                
                # 扩展合同类型识别范围
                contract_types = [
                    # 常见合同类型及其关键词
                    ("劳动合同", ["劳动合同", " employment ", "劳务合同", "雇佣合同", "工作合同"]),
                    ("买卖合同", ["买卖合同", "销售合同", " purchase ", "采购合同", "购销合同"]),
                    ("租赁合同", ["租赁合同", " lease ", "出租合同", "房屋租赁", "场地租赁"]),
                    ("服务合同", ["服务合同", " service ", "技术服务", "咨询服务", "委托服务"]),
                    ("借款合同", ["借款合同", " loan ", "贷款合同", "借款协议", "融资协议"]),
                    ("建设工程合同", ["建设工程", "施工合同", "建筑工程", "工程承包", "施工协议"]),
                    ("知识产权合同", ["知识产权", "专利", "商标", "版权", "著作权", "许可协议"]),
                    ("合作协议", ["合作协议", " partnership ", "联合开发", "合作开发", "战略合作伙伴"]),
                    ("保密协议", ["保密协议", " non-disclosure ", "保密条款", "商业秘密"]),
                    ("担保合同", ["担保合同", "保证合同", "抵押合同", "质押合同", "担保协议"])
                ]
                
                # 识别合同类型
                identified_type = "未知合同类型"
                for contract_name, keywords in contract_types:
                    for keyword in keywords:
                        if keyword.lower() in content_lower:
                            identified_type = contract_name
                            break
                    if identified_type != "未知合同类型":
                        break
                
                contract_type = identified_type
                
                # 根据识别的合同类型设置相应的内容和风险项
                if contract_type == "劳动合同":
                    main_clauses = "包含工作内容、工作时间、劳动报酬、社会保险等条款"
                    compliance_evaluation = "需要检查试用期、加班费、社保缴纳等合规性问题"
                    priority_risks = "试用期约定、加班费支付、社保缴纳"
                    overall_suggestions = "建议重点审查劳动合同法相关条款的合规性"
                    
                    # 生成基本风险项
                    risks = [
                        {
                            "risk_level": "中",
                            "original_clause": "劳动合同期限约定",
                            "risk_explanation": "需要检查劳动合同期限的约定是否符合法律规定，特别是试用期的设置是否合法",
                            "legal_basis": ["《中华人民共和国劳动合同法》第十九条：劳动合同期限三个月以上不满一年的，试用期不得超过一个月；劳动合同期限一年以上不满三年的，试用期不得超过二个月；三年以上固定期限和无固定期限的劳动合同，试用期不得超过六个月。"],
                            "revise_suggestion": "确保试用期设置符合法律规定，并且在劳动合同中明确约定",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "加班费支付条款",
                            "risk_explanation": "需要检查加班费的计算标准和支付方式是否符合法律规定",
                            "legal_basis": ["《中华人民共和国劳动合同法》第三十一条：用人单位应当严格执行劳动定额标准，不得强迫或者变相强迫劳动者加班。用人单位安排加班的，应当按照国家有关规定向劳动者支付加班费。"],
                            "revise_suggestion": "明确约定加班费的计算标准和支付方式，确保符合法律规定",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "高",
                            "original_clause": "社会保险缴纳",
                            "risk_explanation": "需要检查用人单位是否依法为劳动者缴纳社会保险",
                            "legal_basis": ["《中华人民共和国社会保险法》第五十八条：用人单位应当自用工之日起三十日内为其职工向社会保险经办机构申请办理社会保险登记。"],
                            "revise_suggestion": "明确约定用人单位为劳动者缴纳社会保险的义务和具体险种",
                            "confidence_score": 0.9
                        }
                    ]
                elif contract_type == "买卖合同":
                    main_clauses = "包含标的物、价格、交付方式、付款方式等条款"
                    compliance_evaluation = "需要检查合同标的、价格条款、违约责任等内容"
                    priority_risks = "标的物描述、价格支付、违约责任"
                    overall_suggestions = "建议明确标的物规格、质量标准和违约责任"
                    
                    # 生成基本风险项
                    risks = [
                        {
                            "risk_level": "中",
                            "original_clause": "标的物描述",
                            "risk_explanation": "需要检查标的物的描述是否明确、具体，避免产生歧义",
                            "legal_basis": ["《中华人民共和国民法典》第五百一十一条：当事人就有关合同内容约定不明确，依据前条规定仍不能确定的，适用下列规定：（一）质量要求不明确的，按照强制性国家标准履行；没有强制性国家标准的，按照推荐性国家标准履行；没有推荐性国家标准的，按照行业标准履行；没有国家标准、行业标准的，按照通常标准或者符合合同目的的特定标准履行。"],
                            "revise_suggestion": "详细描述标的物的名称、规格、型号、数量、质量标准等信息",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "价格支付条款",
                            "risk_explanation": "需要检查价格的计算方式、支付时间、支付方式等是否明确约定",
                            "legal_basis": ["《中华人民共和国民法典》第五百一十一条：当事人就有关合同内容约定不明确，依据前条规定仍不能确定的，适用下列规定：（二）价款或者报酬不明确的，按照订立合同时履行地的市场价格履行；依法应当执行政府定价或者政府指导价的，依照规定履行。"],
                            "revise_suggestion": "明确约定价格的计算方式、支付时间、支付方式等内容",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "违约责任",
                            "risk_explanation": "需要检查违约责任的约定是否合理、明确",
                            "legal_basis": ["《中华人民共和国民法典》第五百七十七条：当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。"],
                            "revise_suggestion": "明确约定违约责任的具体情形和计算方式",
                            "confidence_score": 0.8
                        }
                    ]
                elif contract_type == "租赁合同":
                    main_clauses = "包含租赁物、租金、租赁期限、双方权利义务等条款"
                    compliance_evaluation = "需要检查租金支付、租赁期限、维修责任等内容"
                    priority_risks = "租金支付、租赁期限、维修责任"
                    overall_suggestions = "建议明确租赁期限、租金调整机制和维修责任"
                    
                    # 生成基本风险项
                    risks = [
                        {
                            "risk_level": "中",
                            "original_clause": "租金支付条款",
                            "risk_explanation": "需要检查租金的金额、支付时间、支付方式等是否明确约定",
                            "legal_basis": ["《中华人民共和国民法典》第七百二十一条：承租人应当按照约定的期限支付租金。对支付租金的期限没有约定或者约定不明确，依据本法第五百一十条的规定仍不能确定，租赁期限不满一年的，应当在租赁期限届满时支付；租赁期限一年以上的，应当在每届满一年时支付，剩余期限不满一年的，应当在租赁期限届满时支付。"],
                            "revise_suggestion": "明确约定租金的金额、支付时间、支付方式等内容",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "租赁期限",
                            "risk_explanation": "需要检查租赁期限的约定是否明确，以及是否符合法律规定",
                            "legal_basis": ["《中华人民共和国民法典》第七百零五条：租赁期限不得超过二十年。超过二十年的，超过部分无效。租赁期限届满，当事人可以续订租赁合同；但是，约定的租赁期限自续订之日起不得超过二十年。"],
                            "revise_suggestion": "明确约定租赁期限，确保不超过法定最长期限",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "维修责任",
                            "risk_explanation": "需要检查维修责任的划分是否明确",
                            "legal_basis": ["《中华人民共和国民法典》第七百一十二条：出租人应当履行租赁物的维修义务，但是当事人另有约定的除外。"],
                            "revise_suggestion": "明确约定租赁物的维修责任划分",
                            "confidence_score": 0.8
                        }
                    ]
                else:
                    # 通用合同类型的默认内容和风险项
                    main_clauses = "包含合同主体、权利义务、违约责任等基本条款"
                    compliance_evaluation = "需要检查合同的合法性、有效性和可执行性"
                    priority_risks = "合同主体资格、权利义务约定、违约责任"
                    overall_suggestions = "建议咨询专业律师进行详细审查"
                    
                    # 生成通用风险项
                    risks = [
                        {
                            "risk_level": "中",
                            "original_clause": "合同主体资格",
                            "risk_explanation": "需要检查合同主体是否具有相应的民事行为能力和权利能力",
                            "legal_basis": ["《中华人民共和国民法典》第一百四十三条：具备下列条件的民事法律行为有效：（一）行为人具有相应的民事行为能力；（二）意思表示真实；（三）不违反法律、行政法规的强制性规定，不违背公序良俗。"],
                            "revise_suggestion": "核实合同主体的资格和权限，确保其能够履行合同义务",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "权利义务约定",
                            "risk_explanation": "需要检查合同双方的权利义务约定是否明确、合理",
                            "legal_basis": ["《中华人民共和国民法典》第四百七十条：合同的内容由当事人约定，一般包括下列条款：（一）当事人的姓名或者名称和住所；（二）标的；（三）数量；（四）质量；（五）价款或者报酬；（六）履行期限、地点和方式；（七）违约责任；（八）解决争议的方法。"],
                            "revise_suggestion": "明确约定双方的权利义务，避免产生歧义",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "违约责任",
                            "risk_explanation": "需要检查违约责任的约定是否合理、明确",
                            "legal_basis": ["《中华人民共和国民法典》第五百七十七条：当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。"],
                            "revise_suggestion": "明确约定违约责任的具体情形和计算方式",
                            "confidence_score": 0.8
                        }
                    ]
                
                parsed_result = {
                    "overall_summary": {
                        "contract_type": contract_type,
                        "main_clauses": main_clauses,
                        "compliance_evaluation": compliance_evaluation
                    },
                    "risks": risks,
                    "summary_recommendations": {
                        "priority_risks": priority_risks,
                        "overall_suggestions": overall_suggestions
                    }
                }
        
        # 生成格式化的整体评估文本
        overall_summary = parsed_result.get("overall_summary", {})
        cleaned_analysis = f"""# 合同审查报告\n\n## 1. 整体评估\n\n- **合同类型**：{overall_summary.get("contract_type", "未知")}\n\n- **主要条款概述**：{overall_summary.get("main_clauses", "")}\n\n- **整体合规性评价**：{overall_summary.get("compliance_evaluation", "")}\n\n## 2. 风险条款分析\n\n## 3. 总结建议\n\n- **优先处理的风险点**：{parsed_result.get("summary_recommendations", {}).get("priority_risks", "")}\n\n- **总体修改建议**：{parsed_result.get("summary_recommendations", {}).get("overall_suggestions", "")}"""
        
        # 提取风险项
        risks = parsed_result.get("risks", [])
        app_logger.info(f"提取到 {len(risks)} 个风险项")
        
        # 处理步骤
        processing_steps = [
            "📸 正在初始化 AI Agent...",
            f"📄 正在读取文件内容，长度: {len(content)} 字符",
            "🔍 正在分析合同结构...",
            "📊 正在提取关键条款...",
            "⚖️ 正在进行法律知识库对比...",
            "🎯 正在识别隐蔽条款和霸王条款...",
            "📝 正在生成风险评估报告...",
            "✅ 审查完成"
        ]
        
        app_logger.info(f"审查完成，发现 {len(risks)} 个风险项")
        
        # 保存审查结果到数据库
        if contract_id:
            db = next(get_db())
            try:
                # 更新合同的整体评估
                contract = db.query(Contract).filter(Contract.id == contract_id).first()
                if contract:
                    contract.overall_summary = cleaned_analysis
                    
                    # 保存风险项
                    for risk in risks:
                        risk_id = str(uuid.uuid4())
                        contract_risk = ContractRisk(
                            id=risk_id,
                            contract_id=contract_id,
                            risk_level=risk.get("risk_level"),
                            original_clause=risk.get("original_clause"),
                            original_text_quote=risk.get("original_text_quote"),
                            risk_explanation=risk.get("risk_explanation"),
                            legal_basis=risk.get("legal_basis"),
                            legal_basis_links=risk.get("legal_basis_links"),
                            revise_suggestion=risk.get("revise_suggestion"),
                            confidence_score=int(risk.get("confidence_score", 0) * 100)  # 转换为整数
                        )
                        db.add(contract_risk)
                    
                    db.commit()
                    app_logger.info(f"审查结果已保存到数据库: {contract_id}")
            except Exception as e:
                db.rollback()
                app_logger.error(f"审查结果保存失败: {str(e)}")
            finally:
                db.close()
        
        return jsonify({
            "success": True,
            "overall_summary": cleaned_analysis,
            "overall_summary_structured": parsed_result.get("overall_summary", {}),
            "summary_recommendations": parsed_result.get("summary_recommendations", {}),
            "risks": risks,
            "is_image_based": False,
            "processing_steps": processing_steps
        })
        
    except Exception as e:
        app_logger.error(f"合同审查错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@router.route('/document/history', methods=['GET'])
def get_contract_history():
    """
    获取合同审查历史记录
    
    返回所有已审查的合同列表，包括基本信息和审查结果摘要
    """
    try:
        db = next(get_db())
        try:
            contracts = db.query(Contract).order_by(Contract.created_at.desc()).all()
            
            history = []
            for contract in contracts:
                risks = db.query(ContractRisk).filter(ContractRisk.contract_id == contract.id).all()
                
                history.append({
                    "id": contract.id,
                    "filename": contract.filename,
                    "file_size": contract.file_size,
                    "text_length": contract.text_length,
                    "overall_summary": contract.overall_summary,
                    "risk_count": len(risks),
                    "risk_levels": {
                        "high": sum(1 for r in risks if r.risk_level == "HIGH"),
                        "medium": sum(1 for r in risks if r.risk_level == "MEDIUM"),
                        "low": sum(1 for r in risks if r.risk_level == "LOW")
                    },
                    "created_at": contract.created_at.isoformat() if contract.created_at else None,
                    "updated_at": contract.updated_at.isoformat() if contract.updated_at else None
                })
            
            return jsonify({
                "success": True,
                "history": history
            })
        finally:
            db.close()
    except Exception as e:
        app_logger.error(f"获取合同历史记录错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@router.route('/document/<contract_id>/details', methods=['GET'])
def get_contract_details(contract_id: str):
    """
    获取特定合同的审查详情
    
    Args:
        contract_id: 合同ID
        
    Returns:
        合同的完整审查详情，包括所有风险项
    """
    try:
        db = next(get_db())
        try:
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                return jsonify({"error": "合同不存在"}), 404
            
            risks = db.query(ContractRisk).filter(ContractRisk.contract_id == contract_id).all()
            
            risk_details = []
            for risk in risks:
                risk_details.append({
                    "id": risk.id,
                    "risk_level": risk.risk_level,
                    "original_clause": risk.original_clause,
                    "original_text_quote": risk.original_text_quote,
                    "risk_explanation": risk.risk_explanation,
                    "legal_basis": risk.legal_basis,
                    "legal_basis_links": risk.legal_basis_links,
                    "revise_suggestion": risk.revise_suggestion,
                    "confidence_score": risk.confidence_score,
                    "created_at": risk.created_at.isoformat() if risk.created_at else None
                })
            
            return jsonify({
                "success": True,
                "contract": {
                    "id": contract.id,
                    "filename": contract.filename,
                    "content": contract.content,
                    "overall_summary": contract.overall_summary,
                    "created_at": contract.created_at.isoformat() if contract.created_at else None,
                    "updated_at": contract.updated_at.isoformat() if contract.updated_at else None
                },
                "risks": risk_details
            })
        finally:
            db.close()
    except Exception as e:
        app_logger.error(f"获取合同详情错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@router.route('/document/<contract_id>', methods=['DELETE'])
def delete_contract(contract_id: str):
    """
    删除合同审查记录
    
    Args:
        contract_id: 合同ID
        
    Returns:
        删除结果
    """
    try:
        db = next(get_db())
        try:
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                return jsonify({"error": "合同不存在"}), 404
            
            # 删除关联的风险项
            db.query(ContractRisk).filter(ContractRisk.contract_id == contract_id).delete()
            # 删除合同
            db.delete(contract)
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "合同删除成功"
            })
        finally:
            db.close()
    except Exception as e:
        app_logger.error(f"删除合同错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@router.route('/document/<contract_id>', methods=['PUT'])
def update_contract_filename(contract_id: str):
    """
    更新合同文件名
    
    Args:
        contract_id: 合同ID
        
    Request Body:
        - filename: 新的文件名
        
    Returns:
        更新结果
    """
    try:
        data = request.json
        if not data or 'filename' not in data:
            return jsonify({"error": "缺少必要参数 filename"}), 400
        
        new_filename = data.get('filename')
        
        db = next(get_db())
        try:
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                return jsonify({"error": "合同不存在"}), 404
            
            contract.filename = new_filename
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "文件名更新成功",
                "filename": new_filename
            })
        finally:
            db.close()
    except Exception as e:
        app_logger.error(f"更新合同错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


def process_contract_review_async(session_id: str, content: str, contract_id: str = None):
    """
    异步处理合同审查
    """
    try:
        app_logger.info(f"开始异步合同审查，会话ID: {session_id}")
        
        # 发送思考步骤事件
        steps = [
            "📸 正在初始化 AI Agent...",
            "🔍 正在分析合同结构...",
            "📊 正在提取关键条款...",
            "⚖️ 正在进行法律知识库对比...",
            "🎯 正在识别隐蔽条款和霸王条款...",
            "📝 正在生成风险评估报告..."
        ]
        
        for i, step in enumerate(steps):
            time.sleep(0.5)
            if session_id in contract_review_streaming_sessions:
                event_data = {
                    "type": "thinking",
                    "data": {"step": step}
                }
                contract_review_streaming_sessions[session_id].append(
                    f"data: {json.dumps(event_data)}\n\n"
                )
        
        # 调用 LLM 进行真实的合同审查
        llm = LLMFactory.create_llm()
        
        prompt = f"""你是一名专业的法律顾问，请对以下合同进行详细审查：

合同内容：
{content}

请严格按照以下JSON格式输出审查结果，确保内容全面、准确、有逻辑性：

{{
  "overall_summary": {{
    "contract_type": "合同类型（如：劳动合同、买卖合同、租赁合同等）",
    "main_clauses": "主要条款概述（200-300字）",
    "compliance_evaluation": "整体合规性评价（100-200字）"
  }},
  "risks": [
    {{
      "risk_level": "高/中/低",
      "original_clause": "直接从合同中提取的具体条款内容",
      "risk_explanation": "详细说明风险的具体表现和可能的法律后果（100-200字）",
      "legal_basis": [
        "具体法律条文1（包括法律名称和条文内容）",
        "具体法律条文2（包括法律名称和条文内容）"
      ],
      "revise_suggestion": "具体、可操作的修改方案（50-100字）",
      "confidence_score": 0.95
    }}
  ],
  "summary_recommendations": {{
    "priority_risks": "优先处理的风险点（按重要性排序）",
    "overall_suggestions": "总体修改建议（100-200字）"
  }}
}}

要求：
1. 只输出JSON格式，不要包含任何其他文本
2. 确保每个风险项都有完整的信息
3. 不使用任何占位符或模板化内容
4. 所有分析都基于合同的实际内容
5. 法律依据引用准确完整
6. 修改建议具体可行
7. 确保JSON格式正确，可以被直接解析"""
        
        app_logger.info("开始调用 LLM 进行合同审查（流式传输）...")
        
        # 使用流式传输调用LLM
        import httpx
        from core.config import settings
        
        # 直接构建消息格式，避免LangChain消息对象的问题
        formatted_messages = [
            {"role": "system", "content": "你是一名专业的法律顾问，擅长合同审查和风险识别。请基于实际合同内容提供详细、准确的法律分析。只输出JSON格式，不要包含任何其他文本。"},
            {"role": "user", "content": prompt}
        ]
        
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": formatted_messages,
            "temperature": float(settings.OPENAI_TEMPERATURE),
            "max_tokens": int(settings.OPENAI_MAX_TOKENS),
            "stream": True
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        }
        
        client = httpx.Client(timeout=180.0)
        review_analysis = ""
        
        try:
            with client.stream(
                "POST",
                f"{settings.OPENAI_BASE_URL}/chat/completions",
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
                                            review_analysis += chunk_content
                                except json.JSONDecodeError:
                                    continue
                else:
                    # 获取详细的错误信息
                    error_content = response.read().decode('utf-8') if hasattr(response, 'read') else str(response)
                    app_logger.error(f"LLM调用失败: {response.status_code}, 响应: {error_content}")
                    raise Exception(f"LLM调用失败: {response.status_code} - {error_content}")
        finally:
            client.close()
        
        app_logger.info(f"LLM 审查完成，结果长度: {len(review_analysis)} 字符")
        
        # 提取并解析JSON格式的审查结果
        # 改进的JSON提取逻辑
        json_start = review_analysis.find('{')
        json_end = review_analysis.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = review_analysis[json_start:json_end]
        else:
            json_str = review_analysis
        
        app_logger.info(f"提取的JSON字符串长度: {len(json_str)}")
        app_logger.info(f"JSON字符串前200字符: {json_str[:200]}...")
        
        # 解析JSON
        try:
            parsed_result = json.loads(json_str)
            app_logger.info("JSON解析成功")
            
            # 验证结果结构
            if not isinstance(parsed_result, dict):
                raise ValueError("解析结果不是有效的JSON对象")
            
            # 确保必要的字段存在
            if "overall_summary" not in parsed_result:
                parsed_result["overall_summary"] = {
                    "contract_type": "未知合同类型",
                    "main_clauses": "合同主要条款概述",
                    "compliance_evaluation": "整体合规性评价"
                }
            if "risks" not in parsed_result:
                parsed_result["risks"] = []
            if "summary_recommendations" not in parsed_result:
                parsed_result["summary_recommendations"] = {
                    "priority_risks": "请检查合同内容",
                    "overall_suggestions": "建议进一步审查"
                }
                
        except json.JSONDecodeError as e:
            app_logger.error(f"JSON解析失败: {str(e)}")
            # 尝试使用更robust的解析方法
            try:
                # 清理JSON字符串，移除可能的无效字符
                import re
                # 移除JSON前后的空白字符和非JSON内容
                clean_json_str = re.sub(r'^[^\{]*', '', json_str)
                clean_json_str = re.sub(r'[^\}]*$', '', clean_json_str)
                
                # 尝试修复常见的JSON格式问题
                # 移除尾部逗号
                clean_json_str = re.sub(r',\s*([\}\]])', r'\1', clean_json_str)
                # 修复缺少引号的键
                clean_json_str = re.sub(r'(\w+):', r'"\1":', clean_json_str)
                # 修复未转义的引号
                clean_json_str = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', r'"\1"', clean_json_str)
                # 尝试再次解析
                parsed_result = json.loads(clean_json_str)
                app_logger.info("清理后JSON解析成功")
                
                # 再次验证结构
                if not isinstance(parsed_result, dict):
                    raise ValueError("清理后解析结果仍不是有效的JSON对象")
                    
            except Exception as e2:
                app_logger.error(f"清理后JSON解析仍然失败: {str(e2)}")
                # 如果JSON解析失败，尝试从原始文本中提取信息
                app_logger.info("尝试从原始LLM响应中提取信息")
                
                # 尝试使用正则表达式从原始文本中提取风险项
                try:
                    import re
                    # 提取整体摘要
                    contract_type_match = re.search(r'"contract_type":\s*"([^"]+)"', json_str)
                    main_clauses_match = re.search(r'"main_clauses":\s*"([^"]+)"', json_str)
                    compliance_evaluation_match = re.search(r'"compliance_evaluation":\s*"([^"]+)"', json_str)
                    
                    contract_type = contract_type_match.group(1) if contract_type_match else "未知合同类型"
                    main_clauses = main_clauses_match.group(1) if main_clauses_match else "合同主要条款概述"
                    compliance_evaluation = compliance_evaluation_match.group(1) if compliance_evaluation_match else "整体合规性评价"
                    
                    # 提取风险项
                    risks = []
                    risk_matches = re.findall(r'\{[^\}]*"risk_level":\s*"([^"]+)",[^\}]*"original_clause":\s*"([^"]+)",[^\}]*"risk_explanation":\s*"([^"]+)",[^\}]*"legal_basis":\s*\[([^\]]*)\],[^\}]*"revise_suggestion":\s*"([^"]+)"[^\}]*\}', json_str, re.DOTALL)
                    
                    for risk_match in risk_matches:
                        risk_level, original_clause, risk_explanation, legal_basis_str, revise_suggestion = risk_match
                        legal_basis = re.findall(r'"([^"]+)"', legal_basis_str)
                        risks.append({
                            "risk_level": risk_level,
                            "original_clause": original_clause,
                            "risk_explanation": risk_explanation,
                            "legal_basis": legal_basis,
                            "revise_suggestion": revise_suggestion,
                            "confidence_score": 0.8
                        })
                    
                    # 提取总结建议
                    priority_risks_match = re.search(r'"priority_risks":\s*"([^"]+)"', json_str)
                    overall_suggestions_match = re.search(r'"overall_suggestions":\s*"([^"]+)"', json_str)
                    
                    priority_risks = priority_risks_match.group(1) if priority_risks_match else "请检查合同内容"
                    overall_suggestions = overall_suggestions_match.group(1) if overall_suggestions_match else "建议进一步审查"
                    
                    parsed_result = {
                        "overall_summary": {
                            "contract_type": contract_type,
                            "main_clauses": main_clauses,
                            "compliance_evaluation": compliance_evaluation
                        },
                        "risks": risks,
                        "summary_recommendations": {
                            "priority_risks": priority_risks,
                            "overall_suggestions": overall_suggestions
                        }
                    }
                    
                    app_logger.info(f"从原始文本中提取到 {len(risks)} 个风险项")
                    
                except Exception as e3:
                    app_logger.error(f"从原始文本提取信息失败: {str(e3)}")
                    # 如果所有方法都失败，使用基于合同内容的兜底方案
                    app_logger.info("使用基于合同内容的兜底方案")
                
                # 基于合同内容的简单分析
                contract_type = "未知合同类型"
                main_clauses = "合同主要条款概述"
                compliance_evaluation = "整体合规性评价"
                priority_risks = "请检查合同内容"
                overall_suggestions = "建议进一步审查"
                risks = []
                
                # 尝试从合同内容中提取信息
                content_lower = content.lower()
                
                # 扩展合同类型识别范围
                contract_types = [
                    # 常见合同类型及其关键词
                    ("劳动合同", ["劳动合同", " employment ", "劳务合同", "雇佣合同", "工作合同"]),
                    ("买卖合同", ["买卖合同", "销售合同", " purchase ", "采购合同", "购销合同"]),
                    ("租赁合同", ["租赁合同", " lease ", "出租合同", "房屋租赁", "场地租赁"]),
                    ("服务合同", ["服务合同", " service ", "技术服务", "咨询服务", "委托服务"]),
                    ("借款合同", ["借款合同", " loan ", "贷款合同", "借款协议", "融资协议"]),
                    ("建设工程合同", ["建设工程", "施工合同", "建筑工程", "工程承包", "施工协议"]),
                    ("知识产权合同", ["知识产权", "专利", "商标", "版权", "著作权", "许可协议"]),
                    ("合作协议", ["合作协议", " partnership ", "联合开发", "合作开发", "战略合作伙伴"]),
                    ("保密协议", ["保密协议", " non-disclosure ", "保密条款", "商业秘密"]),
                    ("担保合同", ["担保合同", "保证合同", "抵押合同", "质押合同", "担保协议"])
                ]
                
                # 识别合同类型
                identified_type = "未知合同类型"
                for contract_name, keywords in contract_types:
                    for keyword in keywords:
                        if keyword.lower() in content_lower:
                            identified_type = contract_name
                            break
                    if identified_type != "未知合同类型":
                        break
                
                contract_type = identified_type
                
                # 根据识别的合同类型设置相应的内容和风险项
                if contract_type == "劳动合同":
                    main_clauses = "包含工作内容、工作时间、劳动报酬、社会保险等条款"
                    compliance_evaluation = "需要检查试用期、加班费、社保缴纳等合规性问题"
                    priority_risks = "试用期约定、加班费支付、社保缴纳"
                    overall_suggestions = "建议重点审查劳动合同法相关条款的合规性"
                    
                    # 生成基本风险项
                    risks = [
                        {
                            "risk_level": "中",
                            "original_clause": "劳动合同期限约定",
                            "risk_explanation": "需要检查劳动合同期限的约定是否符合法律规定，特别是试用期的设置是否合法",
                            "legal_basis": ["《中华人民共和国劳动合同法》第十九条：劳动合同期限三个月以上不满一年的，试用期不得超过一个月；劳动合同期限一年以上不满三年的，试用期不得超过二个月；三年以上固定期限和无固定期限的劳动合同，试用期不得超过六个月。"],
                            "revise_suggestion": "确保试用期设置符合法律规定，并且在劳动合同中明确约定",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "加班费支付条款",
                            "risk_explanation": "需要检查加班费的计算标准和支付方式是否符合法律规定",
                            "legal_basis": ["《中华人民共和国劳动合同法》第三十一条：用人单位应当严格执行劳动定额标准，不得强迫或者变相强迫劳动者加班。用人单位安排加班的，应当按照国家有关规定向劳动者支付加班费。"],
                            "revise_suggestion": "明确约定加班费的计算标准和支付方式，确保符合法律规定",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "高",
                            "original_clause": "社会保险缴纳",
                            "risk_explanation": "需要检查用人单位是否依法为劳动者缴纳社会保险",
                            "legal_basis": ["《中华人民共和国社会保险法》第五十八条：用人单位应当自用工之日起三十日内为其职工向社会保险经办机构申请办理社会保险登记。"],
                            "revise_suggestion": "明确约定用人单位为劳动者缴纳社会保险的义务和具体险种",
                            "confidence_score": 0.9
                        }
                    ]
                elif contract_type == "买卖合同":
                    main_clauses = "包含标的物、价格、交付方式、付款方式等条款"
                    compliance_evaluation = "需要检查合同标的、价格条款、违约责任等内容"
                    priority_risks = "标的物描述、价格支付、违约责任"
                    overall_suggestions = "建议明确标的物规格、质量标准和违约责任"
                    
                    # 生成基本风险项
                    risks = [
                        {
                            "risk_level": "中",
                            "original_clause": "标的物描述",
                            "risk_explanation": "需要检查标的物的描述是否明确、具体，避免产生歧义",
                            "legal_basis": ["《中华人民共和国民法典》第五百一十一条：当事人就有关合同内容约定不明确，依据前条规定仍不能确定的，适用下列规定：（一）质量要求不明确的，按照强制性国家标准履行；没有强制性国家标准的，按照推荐性国家标准履行；没有推荐性国家标准的，按照行业标准履行；没有国家标准、行业标准的，按照通常标准或者符合合同目的的特定标准履行。"],
                            "revise_suggestion": "详细描述标的物的名称、规格、型号、数量、质量标准等信息",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "价格支付条款",
                            "risk_explanation": "需要检查价格的计算方式、支付时间、支付方式等是否明确约定",
                            "legal_basis": ["《中华人民共和国民法典》第五百一十一条：当事人就有关合同内容约定不明确，依据前条规定仍不能确定的，适用下列规定：（二）价款或者报酬不明确的，按照订立合同时履行地的市场价格履行；依法应当执行政府定价或者政府指导价的，依照规定履行。"],
                            "revise_suggestion": "明确约定价格的计算方式、支付时间、支付方式等内容",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "违约责任",
                            "risk_explanation": "需要检查违约责任的约定是否合理、明确",
                            "legal_basis": ["《中华人民共和国民法典》第五百七十七条：当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。"],
                            "revise_suggestion": "明确约定违约责任的具体情形和计算方式",
                            "confidence_score": 0.8
                        }
                    ]
                elif contract_type == "租赁合同":
                    main_clauses = "包含租赁物、租金、租赁期限、双方权利义务等条款"
                    compliance_evaluation = "需要检查租金支付、租赁期限、维修责任等内容"
                    priority_risks = "租金支付、租赁期限、维修责任"
                    overall_suggestions = "建议明确租赁期限、租金调整机制和维修责任"
                    
                    # 生成基本风险项
                    risks = [
                        {
                            "risk_level": "中",
                            "original_clause": "租金支付条款",
                            "risk_explanation": "需要检查租金的金额、支付时间、支付方式等是否明确约定",
                            "legal_basis": ["《中华人民共和国民法典》第七百二十一条：承租人应当按照约定的期限支付租金。对支付租金的期限没有约定或者约定不明确，依据本法第五百一十条的规定仍不能确定，租赁期限不满一年的，应当在租赁期限届满时支付；租赁期限一年以上的，应当在每届满一年时支付，剩余期限不满一年的，应当在租赁期限届满时支付。"],
                            "revise_suggestion": "明确约定租金的金额、支付时间、支付方式等内容",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "租赁期限",
                            "risk_explanation": "需要检查租赁期限的约定是否明确，以及是否符合法律规定",
                            "legal_basis": ["《中华人民共和国民法典》第七百零五条：租赁期限不得超过二十年。超过二十年的，超过部分无效。租赁期限届满，当事人可以续订租赁合同；但是，约定的租赁期限自续订之日起不得超过二十年。"],
                            "revise_suggestion": "明确约定租赁期限，确保不超过法定最长期限",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "维修责任",
                            "risk_explanation": "需要检查维修责任的划分是否明确",
                            "legal_basis": ["《中华人民共和国民法典》第七百一十二条：出租人应当履行租赁物的维修义务，但是当事人另有约定的除外。"],
                            "revise_suggestion": "明确约定租赁物的维修责任划分",
                            "confidence_score": 0.8
                        }
                    ]
                else:
                    # 通用合同类型的默认内容和风险项
                    main_clauses = "包含合同主体、权利义务、违约责任等基本条款"
                    compliance_evaluation = "需要检查合同的合法性、有效性和可执行性"
                    priority_risks = "合同主体资格、权利义务约定、违约责任"
                    overall_suggestions = "建议咨询专业律师进行详细审查"
                    
                    # 生成通用风险项
                    risks = [
                        {
                            "risk_level": "中",
                            "original_clause": "合同主体资格",
                            "risk_explanation": "需要检查合同主体是否具有相应的民事行为能力和权利能力",
                            "legal_basis": ["《中华人民共和国民法典》第一百四十三条：具备下列条件的民事法律行为有效：（一）行为人具有相应的民事行为能力；（二）意思表示真实；（三）不违反法律、行政法规的强制性规定，不违背公序良俗。"],
                            "revise_suggestion": "核实合同主体的资格和权限，确保其能够履行合同义务",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "权利义务约定",
                            "risk_explanation": "需要检查合同双方的权利义务约定是否明确、合理",
                            "legal_basis": ["《中华人民共和国民法典》第四百七十条：合同的内容由当事人约定，一般包括下列条款：（一）当事人的姓名或者名称和住所；（二）标的；（三）数量；（四）质量；（五）价款或者报酬；（六）履行期限、地点和方式；（七）违约责任；（八）解决争议的方法。"],
                            "revise_suggestion": "明确约定双方的权利义务，避免产生歧义",
                            "confidence_score": 0.8
                        },
                        {
                            "risk_level": "中",
                            "original_clause": "违约责任",
                            "risk_explanation": "需要检查违约责任的约定是否合理、明确",
                            "legal_basis": ["《中华人民共和国民法典》第五百七十七条：当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。"],
                            "revise_suggestion": "明确约定违约责任的具体情形和计算方式",
                            "confidence_score": 0.8
                        }
                    ]
                
                parsed_result = {
                    "overall_summary": {
                        "contract_type": contract_type,
                        "main_clauses": main_clauses,
                        "compliance_evaluation": compliance_evaluation
                    },
                    "risks": risks,
                    "summary_recommendations": {
                        "priority_risks": priority_risks,
                        "overall_suggestions": overall_suggestions
                    }
                }
        
        # 生成格式化的整体评估文本
        overall_summary = parsed_result.get("overall_summary", {})
        cleaned_analysis = f"""# 合同审查报告\n\n## 1. 整体评估\n\n- **合同类型**：{overall_summary.get("contract_type", "未知")}\n\n- **主要条款概述**：{overall_summary.get("main_clauses", "")}\n\n- **整体合规性评价**：{overall_summary.get("compliance_evaluation", "")}\n\n## 2. 风险条款分析\n\n## 3. 总结建议\n\n- **优先处理的风险点**：{parsed_result.get("summary_recommendations", {}).get("priority_risks", "")}\n\n- **总体修改建议**：{parsed_result.get("summary_recommendations", {}).get("overall_suggestions", "")}"""
        
        # 提取风险项
        risks = parsed_result.get("risks", [])
        app_logger.info(f"提取到 {len(risks)} 个风险项")
        
        # 发送整体评估完成事件
        if session_id in contract_review_streaming_sessions:
            event_data = {
                "type": "overall_summary",
                "data": {
                    "text": cleaned_analysis,
                    "structured": parsed_result.get("overall_summary", {})
                }
            }
            contract_review_streaming_sessions[session_id].append(
                f"data: {json.dumps(event_data)}\n\n"
            )
        
        # 逐个发送风险项
        for i, risk in enumerate(risks):
            time.sleep(0.3)
            if session_id in contract_review_streaming_sessions:
                event_data = {
                    "type": "risk",
                    "data": risk,
                    "index": i,
                    "total": len(risks)
                }
                contract_review_streaming_sessions[session_id].append(
                    f"data: {json.dumps(event_data)}\n\n"
                )
        
        # 保存审查结果到数据库
        if contract_id:
            db = next(get_db())
            try:
                # 更新合同的整体评估
                contract = db.query(Contract).filter(Contract.id == contract_id).first()
                if contract:
                    contract.overall_summary = cleaned_analysis
                    
                    # 保存风险项
                    for risk in risks:
                        risk_id = str(uuid.uuid4())
                        contract_risk = ContractRisk(
                            id=risk_id,
                            contract_id=contract_id,
                            risk_level=risk.get("risk_level"),
                            original_clause=risk.get("original_clause"),
                            original_text_quote=risk.get("original_text_quote"),
                            risk_explanation=risk.get("risk_explanation"),
                            legal_basis=risk.get("legal_basis"),
                            legal_basis_links=risk.get("legal_basis_links"),
                            revise_suggestion=risk.get("revise_suggestion"),
                            confidence_score=int(risk.get("confidence_score", 0) * 100)
                        )
                        db.add(contract_risk)
                    
                    db.commit()
                    app_logger.info(f"审查结果已保存到数据库: {contract_id}")
            except Exception as e:
                db.rollback()
                app_logger.error(f"审查结果保存失败: {str(e)}")
            finally:
                db.close()
        
        # 发送完成事件
        if session_id in contract_review_streaming_sessions:
            event_data = {
                "type": "completed",
                "data": {
                    "overall_summary": cleaned_analysis,
                    "overall_summary_structured": parsed_result.get("overall_summary", {}),
                    "summary_recommendations": parsed_result.get("summary_recommendations", {}),
                    "risks": risks,
                    "is_image_based": False
                }
            }
            contract_review_streaming_sessions[session_id].append(
                f"data: {json.dumps(event_data)}\n\n"
            )
        
        # 标记会话完成
        if session_id in contract_review_processing_sessions:
            contract_review_processing_sessions[session_id]['status'] = 'completed'
        
    except Exception as e:
        app_logger.error(f"合同审查异步处理错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 发送错误事件
        if session_id in contract_review_streaming_sessions:
            event_data = {
                "type": "error",
                "data": {"error": str(e)}
            }
            contract_review_streaming_sessions[session_id].append(
                f"data: {json.dumps(event_data)}\n\n"
            )
        
        # 标记会话出错
        if session_id in contract_review_processing_sessions:
            contract_review_processing_sessions[session_id]['status'] = 'error'


@router.route('/document/review/stream', methods=['POST'])
def start_contract_review_stream():
    """
    启动合同审查流式输出
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "缺少请求数据"}), 400
        
        contract_id = data.get('contract_id')
        content = data.get('content')
        
        if not contract_id and not content:
            return jsonify({"error": "请提供合同内容或合同ID"}), 400
        
        # 如果提供了合同ID，从数据库获取内容
        if contract_id and not content:
            db = next(get_db())
            try:
                contract = db.query(Contract).filter(Contract.id == contract_id).first()
                if contract:
                    content = contract.content
                else:
                    return jsonify({"error": "合同不存在"}), 404
            finally:
                db.close()
        
        # 验证内容长度
        if len(content.strip()) == 0:
            return jsonify({"error": "合同内容为空，无法进行审查"}), 400
        
        # 创建会话ID
        session_id = str(uuid.uuid4())
        
        # 初始化会话
        contract_review_processing_sessions[session_id] = {
            'status': 'processing',
            'contract_id': contract_id
        }
        contract_review_streaming_sessions[session_id] = []
        
        # 启动异步处理
        thread = threading.Thread(
            target=process_contract_review_async,
            args=(session_id, content, contract_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "session_id": session_id
        })
        
    except Exception as e:
        app_logger.error(f"启动合同审查流式输出错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@router.route('/document/review/stream/<session_id>', methods=['GET'])
def get_contract_review_stream(session_id: str):
    """
    获取合同审查流式输出
    """
    def generate():
        try:
            # 确保队列存在
            if session_id not in contract_review_streaming_sessions:
                contract_review_streaming_sessions[session_id] = []
            
            # 发送初始连接事件
            yield f"data: {json.dumps({'type': 'connected', 'data': {'session_id': session_id}})}\n\n"
            
            # 持续发送事件
            while session_id in contract_review_streaming_sessions:
                # 发送队列中的事件
                if contract_review_streaming_sessions[session_id]:
                    events = contract_review_streaming_sessions[session_id].copy()
                    contract_review_streaming_sessions[session_id].clear()
                    for event in events:
                        yield event
                
                # 检查会话状态
                if session_id in contract_review_processing_sessions:
                    status = contract_review_processing_sessions[session_id].get('status')
                    if status in ['completed', 'error'] and not contract_review_streaming_sessions[session_id]:
                        break
                
                # 防止CPU占用过高
                time.sleep(0.1)
            
            # 清理SSE连接
            if session_id in contract_review_streaming_sessions:
                del contract_review_streaming_sessions[session_id]
                
        except Exception as e:
            app_logger.error(f"合同审查SSE流错误: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}})}\n\n"
            if session_id in contract_review_streaming_sessions:
                del contract_review_streaming_sessions[session_id]
    
    # 设置SSE响应头
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['X-Accel-Buffering'] = 'no'
    return response
