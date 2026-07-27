"""案件工作台多格式材料识别的边界测试。"""

import io
import unittest
from unittest.mock import Mock, patch

from flask import Flask

from routers import digital_human_agent
from services.material_extraction import MaterialExtractionError, extract_material_text


class MaterialExtractionTest(unittest.TestCase):
    def test_utf8_txt_is_returned_as_editable_preview(self):
        result = extract_material_text(
            "工资记录.txt",
            io.BytesIO("2026年5月工资尚未支付。".encode("utf-8")),
        )
        self.assertEqual(result["filename"], "工资记录.txt")
        self.assertEqual(result["media_type"], "text/plain")
        self.assertIn("工资尚未支付", result["text"])

    def test_unsupported_extension_fails_instead_of_creating_placeholder(self):
        with self.assertRaisesRegex(MaterialExtractionError, "不支持"):
            extract_material_text("证据.exe", io.BytesIO(b"not evidence"))

    def test_pdf_and_docx_are_extracted_to_the_same_preview_contract(self):
        try:
            import fitz
            from docx import Document
        except ImportError:
            self.skipTest("文档解析依赖未安装")

        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "salary record 2026-05")
        pdf_result = extract_material_text("工资记录.pdf", io.BytesIO(pdf.tobytes()))
        pdf.close()

        document = Document()
        document.add_paragraph("2026年5月工资尚未支付")
        docx_bytes = io.BytesIO()
        document.save(docx_bytes)
        docx_bytes.seek(0)
        docx_result = extract_material_text("劳动合同.docx", docx_bytes)

        self.assertIn("salary record", pdf_result["text"])
        self.assertIn("工资尚未支付", docx_result["text"])

    def test_organize_endpoint_validates_matter_and_does_not_persist_preview(self):
        facade = Mock()
        facade.get_matter.return_value = {"matter_id": "matter_test"}
        app = Flask(__name__)
        app.register_blueprint(digital_human_agent.router, url_prefix="/api")

        with patch.object(digital_human_agent, "get_legal_agent_facade", return_value=facade):
            response = app.test_client().post(
                "/api/digital-human/agent/matters/matter_test/materials/organize",
                headers={"X-Digital-Human-Client-ID": "dhc_material_test"},
                data={"file": (io.BytesIO("欠薪两个月".encode("utf-8")), "说明.txt")},
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["material"]["text"], "欠薪两个月")
        facade.get_matter.assert_called_once_with("matter_test", "dhc_material_test")
        facade.add_material.assert_not_called()


if __name__ == "__main__":
    unittest.main()
