"""
MOSS Language Abstraction Layer
================================

多语言支持的抽象接口，为未来扩展到 JavaScript、Go 等语言做准备。

Architecture:
    LanguageParser      - 语言解析抽象
    LanguageAnalyzer    - 语言分析抽象
    LanguageRefactorer  - 语言重构抽象
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum


class LanguageType(Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"


@dataclass
class ParseResult:
    """解析结果"""
    file_path: str
    language: LanguageType
    success: bool
    ast: Optional[Any] = None
    errors: List[str] = None
    symbols: List[str] = None
    imports: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.symbols is None:
            self.symbols = []
        if self.imports is None:
            self.imports = []


@dataclass
class AnalysisResult:
    """分析结果"""
    file_path: str
    language: LanguageType
    issues: List[Dict[str, Any]]
    complexity: int = 0
    maintainability_index: float = 0.0
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []


@dataclass
class RefactorResult:
    """重构结果"""
    file_path: str
    language: LanguageType
    success: bool
    changes: List[Dict[str, Any]]
    original_content: str = ""
    new_content: str = ""
    
    def __post_init__(self):
        if self.changes is None:
            self.changes = []


class LanguageParser(ABC):
    """语言解析抽象基类"""
    
    @abstractmethod
    def parse(self, content: str, file_path: str) -> ParseResult:
        """解析代码内容"""
        pass
    
    @abstractmethod
    def get_supported_language(self) -> LanguageType:
        """获取支持的语言类型"""
        pass
    
    @abstractmethod
    def extract_symbols(self, ast: Any) -> List[str]:
        """提取符号（函数、类、变量名）"""
        pass
    
    @abstractmethod
    def extract_imports(self, ast: Any) -> List[str]:
        """提取导入"""
        pass
    
    @abstractmethod
    def get_syntax_errors(self, content: str) -> List[str]:
        """检测语法错误"""
        pass


class LanguageAnalyzer(ABC):
    """语言分析抽象基类"""
    
    @abstractmethod
    def analyze(self, parse_result: ParseResult) -> AnalysisResult:
        """分析代码"""
        pass
    
    @abstractmethod
    def get_supported_language(self) -> LanguageType:
        """获取支持的语言类型"""
        pass
    
    @abstractmethod
    def detect_unused_imports(self, parse_result: ParseResult) -> List[str]:
        """检测未使用的导入"""
        pass
    
    @abstractmethod
    def detect_long_functions(self, parse_result: ParseResult, threshold: int = 50) -> List[Dict]:
        """检测过长的函数"""
        pass
    
    @abstractmethod
    def detect_high_complexity(self, parse_result: ParseResult, threshold: int = 10) -> List[Dict]:
        """检测高复杂度"""
        pass
    
    @abstractmethod
    def calculate_complexity(self, parse_result: ParseResult) -> int:
        """计算代码复杂度"""
        pass


class LanguageRefactorer(ABC):
    """语言重构抽象基类"""
    
    @abstractmethod
    def refactor(self, parse_result: ParseResult, operation: str, params: Dict) -> RefactorResult:
        """执行重构"""
        pass
    
    @abstractmethod
    def get_supported_language(self) -> LanguageType:
        """获取支持的语言类型"""
        pass
    
    @abstractmethod
    def organize_imports(self, content: str) -> str:
        """整理导入"""
        pass
    
    @abstractmethod
    def extract_function(self, content: str, start_line: int, end_line: int, name: str) -> str:
        """提取函数"""
        pass
    
    @abstractmethod
    def rename_symbol(self, content: str, old_name: str, new_name: str) -> str:
        """重命名符号"""
        pass


class LanguageRegistry:
    """语言注册中心"""
    
    _parsers: Dict[LanguageType, LanguageParser] = {}
    _analyzers: Dict[LanguageType, LanguageAnalyzer] = {}
    _refactorers: Dict[LanguageType, LanguageRefactorer] = {}
    
    @classmethod
    def register_parser(cls, parser: LanguageParser):
        """注册解析器"""
        cls._parsers[parser.get_supported_language()] = parser
    
    @classmethod
    def register_analyzer(cls, analyzer: LanguageAnalyzer):
        """注册分析器"""
        cls._analyzers[analyzer.get_supported_language()] = analyzer
    
    @classmethod
    def register_refactorer(cls, refactorer: LanguageRefactorer):
        """注册重构器"""
        cls._refactorers[refactorer.get_supported_language()] = refactorer
    
    @classmethod
    def get_parser(cls, language: LanguageType) -> Optional[LanguageParser]:
        """获取解析器"""
        return cls._parsers.get(language)
    
    @classmethod
    def get_analyzer(cls, language: LanguageType) -> Optional[LanguageAnalyzer]:
        """获取分析器"""
        return cls._analyzers.get(language)
    
    @classmethod
    def get_refactorer(cls, language: LanguageType) -> Optional[LanguageRefactorer]:
        """获取重构器"""
        return cls._refactorers.get(language)
    
    @classmethod
    def get_supported_languages(cls) -> List[LanguageType]:
        """获取所有支持的语言"""
        return list(cls._parsers.keys())
    
    @classmethod
    def is_language_supported(cls, language: LanguageType) -> bool:
        """检查语言是否支持"""
        return language in cls._parsers


__all__ = [
    'LanguageType',
    'ParseResult',
    'AnalysisResult',
    'RefactorResult',
    'LanguageParser',
    'LanguageAnalyzer',
    'LanguageRefactorer',
    'LanguageRegistry',
    'PythonParser',
]

# Import PythonParser after __all__ to avoid circular import
from .python_parser import PythonParser