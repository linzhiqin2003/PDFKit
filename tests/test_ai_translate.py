"""AI 翻译功能单元测试"""

import pytest
from pathlib import Path

from pdfkit.ai.image_translator import (
    QwenImageTranslator,
    validate_language_pair,
    LanguageCode,
    TaskStatus,
)
from pdfkit.ai.uploader import (
    create_uploader,
    Base64Uploader,
    LocalUploader,
    UploadMethod,
)
from pdfkit.ai.translator import AITranslator, parse_page_range


class TestValidateLanguagePair:
    """语言对验证测试"""

    def test_valid_zh_to_en(self):
        """测试中文到英文"""
        is_valid, error = validate_language_pair("zh", "en")
        assert is_valid
        assert error is None

    def test_valid_en_to_zh(self):
        """测试英文到中文"""
        is_valid, error = validate_language_pair("en", "zh")
        assert is_valid
        assert error is None

    def test_valid_auto_to_zh(self):
        """测试自动检测到中文"""
        is_valid, error = validate_language_pair("auto", "zh")
        assert is_valid
        assert error is None

    def test_valid_zh_to_ja(self):
        """测试中文到日文"""
        is_valid, error = validate_language_pair("zh", "ja")
        assert is_valid
        assert error is None

    def test_invalid_ja_to_ko(self):
        """测试日文到韩文（没有中文或英文）"""
        is_valid, error = validate_language_pair("ja", "ko")
        assert not is_valid
        assert "中文或英文" in error

    def test_invalid_fr_to_de(self):
        """测试法文到德文（没有中文或英文）"""
        is_valid, error = validate_language_pair("fr", "de")
        assert not is_valid
        assert error is not None


class TestParsePageRange:
    """页面范围解析测试"""

    def test_parse_single_page(self):
        """测试单页"""
        pages = parse_page_range("5", 10)
        assert pages == [4]  # 0-based

    def test_parse_range(self):
        """测试范围"""
        pages = parse_page_range("1-5", 10)
        assert pages == [0, 1, 2, 3, 4]

    def test_parse_mixed(self):
        """测试混合格式"""
        pages = parse_page_range("1-3,5,7-9", 10)
        assert pages == [0, 1, 2, 4, 6, 7, 8]

    def test_parse_out_of_range(self):
        """测试超出范围"""
        pages = parse_page_range("1-5,8-15", 10)
        assert pages == [0, 1, 2, 3, 4, 7, 8, 9]

    def test_parse_duplicates_removed(self):
        """测试去重"""
        pages = parse_page_range("1-3,2-4", 10)
        assert pages == [0, 1, 2, 3]


class TestBase64Uploader:
    """Base64 上传器测试"""

    def test_upload_returns_data_url(self):
        """测试返回 Data URL"""
        uploader = Base64Uploader()
        img_bytes = b"fake_image_data"

        url = uploader.upload(img_bytes, "test.png")

        assert url.startswith("data:image/png;base64,")
        assert "fake_image_data" not in url  # base64 encoded


class TestLocalUploader:
    """本地上传器测试"""

    def test_upload_saves_to_temp(self, tmp_path: Path):
        """测试保存到临时目录"""
        uploader = LocalUploader()
        uploader.temp_dir = tmp_path

        img_bytes = b"test_image_data"
        url = uploader.upload(img_bytes, "test.png")

        # 验证文件被保存
        assert (tmp_path / "test.png").read_bytes() == img_bytes
        assert url.startswith("http://localhost:")


class TestCreateUploader:
    """上传器工厂测试"""

    def test_create_base64_uploader(self):
        """测试创建 Base64 上传器"""
        uploader = create_uploader("base64")
        assert isinstance(uploader, Base64Uploader)

    def test_create_local_uploader(self):
        """测试创建本地上传器"""
        uploader = create_uploader("local", port=9000)
        assert isinstance(uploader, LocalUploader)

    def test_create_invalid_uploader(self):
        """测试无效上传器"""
        with pytest.raises(ValueError, match="不支持的上传方法"):
            create_uploader("invalid")


class TestQwenImageTranslator:
    """图像翻译器测试"""

    def test_init_without_api_key(self, monkeypatch):
        """测试没有 API Key 时初始化"""
        monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

        with pytest.raises(ValueError, match="API Key 未配置"):
            QwenImageTranslator(api_key=None)

    def test_init_with_api_key(self):
        """测试有 API Key 时初始化"""
        translator = QwenImageTranslator(api_key="test_key")
        assert translator.api_key == "test_key"
        assert translator.timeout == 120
        assert translator.poll_interval == 5

    def test_init_custom_params(self):
        """测试自定义参数"""
        translator = QwenImageTranslator(
            api_key="test_key",
            timeout=60,
            poll_interval=10,
        )
        assert translator.timeout == 60
        assert translator.poll_interval == 10


class TestAITranslator:
    """AI 翻译器测试"""

    def test_init_default_params(self):
        """测试默认参数初始化"""
        translator = AITranslator(api_key="test_key")
        assert translator.upload_method == "base64"
        assert translator.dpi == 200
        assert translator.timeout == 120

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        translator = AITranslator(
            api_key="test_key",
            upload_method="local",
            dpi=300,
            timeout=60,
        )
        assert translator.upload_method == "local"
        assert translator.dpi == 300
        assert translator.timeout == 60

    def test_load_glossary(self, tmp_path: Path):
        """测试加载术语表"""
        translator = AITranslator(api_key="test_key")

        glossary_file = tmp_path / "terms.csv"
        glossary_file.write_text("src,tgt\nMachine Learning,机器学习\nNeural Network,神经网络")

        terms = translator._load_glossary(glossary_file)

        assert len(terms) == 2
        assert terms[0] == {"src": "Machine Learning", "tgt": "机器学习"}
        assert terms[1] == {"src": "Neural Network", "tgt": "神经网络"}

    def test_load_glossary_limit_50(self, tmp_path: Path):
        """测试术语表限制为50个"""
        translator = AITranslator(api_key="test_key")

        glossary_file = tmp_path / "terms.csv"
        lines = ["src,tgt"]
        for i in range(100):
            lines.append(f"term{i},翻译{i}")
        glossary_file.write_text("\n".join(lines))

        terms = translator._load_glossary(glossary_file)

        assert len(terms) == 50  # 限制为50个

    def test_load_glossary_skip_empty(self, tmp_path: Path):
        """测试跳过空术语"""
        translator = AITranslator(api_key="test_key")

        glossary_file = tmp_path / "terms.csv"
        glossary_file.write_text("src,tgt\nTerm1,翻译1\n,翻译2\nTerm3,")

        terms = translator._load_glossary(glossary_file)

        assert len(terms) == 1
        assert terms[0] == {"src": "Term1", "tgt": "翻译1"}


@pytest.mark.parametrize("source,target,valid", [
    ("zh", "en", True),
    ("en", "zh", True),
    ("auto", "zh", True),
    ("auto", "en", True),
    ("zh", "ja", True),
    ("en", "ja", True),
    ("ja", "ko", False),
    ("fr", "de", False),
    ("ko", "vi", False),
])
def test_language_pair_validation(source, target, valid):
    """参数化测试语言对验证"""
    is_valid, _ = validate_language_pair(source, target)
    assert is_valid == valid


@pytest.mark.parametrize("range_str,total,expected", [
    ("1", 5, [0]),
    ("1-3", 5, [0, 1, 2]),
    ("1,3,5", 5, [0, 2, 4]),
    ("1-3,5", 5, [0, 1, 2, 4]),
    ("2-4,1", 5, [0, 1, 2, 3]),
])
def test_parse_page_range_cases(range_str, total, expected):
    """参数化测试页面范围解析"""
    result = parse_page_range(range_str, total)
    assert result == expected
