"""共享的案件材料文本识别服务。

只负责把用户上传的原始文件转成可复核文本；不创建纠纷或 Matter，避免跨业务数据串联。
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import BinaryIO

from core.logger import app_logger


MAX_MATERIAL_BYTES = 25 * 1024 * 1024
SUPPORTED_EXTENSIONS = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
}


class MaterialExtractionError(ValueError):
    """材料无法安全、可靠地转换为文字。"""


def extract_material_text(filename: str, stream: BinaryIO) -> dict:
    """读取上传流并返回可由用户复核编辑的纯文本。"""
    safe_name = Path(filename or "").name.strip()[:180]
    extension = Path(safe_name).suffix.lower()
    if not safe_name or extension not in SUPPORTED_EXTENSIONS:
        raise MaterialExtractionError("不支持该文件格式，请上传 TXT、PDF、DOCX、图片、音频或视频")

    content = stream.read(MAX_MATERIAL_BYTES + 1)
    if not content:
        raise MaterialExtractionError("文件内容为空")
    if len(content) > MAX_MATERIAL_BYTES:
        raise MaterialExtractionError("单个文件不能超过 25MB")

    if extension == ".txt":
        text = _decode_text(content)
    elif extension == ".pdf":
        text = _extract_pdf(content)
    elif extension == ".docx":
        text = _extract_docx(content)
    elif extension in {".png", ".jpg", ".jpeg"}:
        text = _extract_image(content)
    else:
        text = _extract_media(content, extension)

    normalized = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    if not normalized:
        raise MaterialExtractionError("没有识别到可用文字，请换一份清晰材料或直接粘贴原文")
    return {
        "filename": safe_name,
        "media_type": SUPPORTED_EXTENSIONS[extension],
        "text": normalized,
        "character_count": len(normalized),
    }


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise MaterialExtractionError("TXT 编码无法识别，请另存为 UTF-8 后重试")


def _extract_pdf(content: bytes) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise MaterialExtractionError("服务器未安装 PDF 解析组件") from exc
    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            return "\n".join(page.get_text("text") for page in document)
    except Exception as exc:
        raise MaterialExtractionError("PDF 无法解析，文件可能损坏或受密码保护") from exc


def _extract_docx(content: bytes) -> str:
    try:
        from docx import Document
        from io import BytesIO
    except ImportError as exc:
        raise MaterialExtractionError("服务器未安装 Word 解析组件") from exc
    try:
        document = Document(BytesIO(content))
        parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        parts.extend(
            "\t".join(cell.text for cell in row.cells)
            for table in document.tables for row in table.rows
        )
        return "\n".join(parts)
    except Exception as exc:
        raise MaterialExtractionError("Word 文档无法解析，请确认文件不是旧版 DOC 或已损坏") from exc


def _extract_image(content: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
        from io import BytesIO
        if not shutil.which("tesseract"):
            bundled = Path(sys.prefix) / "Library" / "bin" / "tesseract.exe"
            if bundled.exists():
                pytesseract.pytesseract.tesseract_cmd = str(bundled)
        tessdata = Path(sys.prefix) / "share" / "tessdata"
        if tessdata.exists():
            os.environ["TESSDATA_PREFIX"] = str(tessdata)
        return pytesseract.image_to_string(Image.open(BytesIO(content)), lang="chi_sim+eng")
    except ImportError as exc:
        raise MaterialExtractionError("服务器未安装图片文字识别组件") from exc
    except Exception as exc:
        app_logger.exception("图片材料 OCR 失败")
        raise MaterialExtractionError("图片文字识别失败，请上传清晰截图或直接粘贴文字") from exc


def _extract_media(content: bytes, extension: str) -> str:
    try:
        import whisper
    except Exception as exc:
        raise MaterialExtractionError("服务器未启用音视频转写组件") from exc

    temporary_path = ""
    try:
        if not shutil.which("ffmpeg"):
            bundled_ffmpeg = Path(sys.prefix) / "Library" / "bin"
            if (bundled_ffmpeg / "ffmpeg.exe").exists():
                os.environ["PATH"] = f"{bundled_ffmpeg}{os.pathsep}{os.environ.get('PATH', '')}"
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temporary:
            temporary.write(content)
            temporary_path = temporary.name
        model = whisper.load_model("base")
        result = model.transcribe(temporary_path, language="zh")
        return str(result.get("text", ""))
    except Exception as exc:
        app_logger.exception("音视频材料转写失败")
        raise MaterialExtractionError("音视频转写失败，请检查文件声音是否清晰或直接粘贴文字") from exc
    finally:
        if temporary_path:
            try:
                os.remove(temporary_path)
            except OSError:
                pass
