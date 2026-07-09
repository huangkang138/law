"""
法律文本分块器
"""

from flask_app.core.logger import app_logger


class LegalChunker:
    """
    法律文本分块器
    """
    
    def __init__(self):
        """
        初始化分块器
        """
        app_logger.info("✅ 法律文本分块器初始化完成")
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """
        分块文本
        
        Args:
            text: 文本内容
            chunk_size: 块大小
            overlap: 重叠大小
            
        Returns:
            分块列表
        """
        try:
            chunks = []
            start = 0
            text_length = len(text)
            
            while start < text_length:
                end = min(start + chunk_size, text_length)
                chunk = text[start:end]
                chunks.append(chunk)
                start += chunk_size - overlap
            
            app_logger.info(f"文本分块完成，共 {len(chunks)} 块")
            return chunks
            
        except Exception as e:
            app_logger.error(f"文本分块错误: {str(e)}")
            raise
