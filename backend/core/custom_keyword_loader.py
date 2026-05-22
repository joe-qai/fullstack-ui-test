import ast
import os
import sys
import importlib.util
from config import settings

CUSTOM_KEYWORDS_DIR = settings.scripts_dir / "custom_keywords"


def ensure_directory():
    os.makedirs(CUSTOM_KEYWORDS_DIR, exist_ok=True)
    init_file = CUSTOM_KEYWORDS_DIR / "__init__.py"
    if not init_file.exists():
        init_file.write_text("", encoding="utf-8")


def validate_code(code: str):
    """Validate Python code syntax using ast.parse."""
    if not code.strip():
        return False, "代码不能为空"
    
    try:
        tree = ast.parse(code)
        
        has_function = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_function = True
                break
        
        if not has_function:
            return False, "代码中需要包含至少一个函数定义"
        
        return True, ""
    except SyntaxError as e:
        line_info = f"第 {e.lineno} 行" if e.lineno else ""
        return False, f"Python syntax error: {line_info}: {e.msg}"
    except Exception as e:
        return False, f"代码验证失败: {str(e)}"


def write_keyword_file(name: str, code: str):
    """Write custom keyword code to a Python module file."""
    ensure_directory()
    file_path = CUSTOM_KEYWORDS_DIR / f"{name}.py"
    file_path.write_text(code, encoding="utf-8")


def load_custom_keyword_function(name: str):
    """Dynamically load a custom keyword function."""
    ensure_directory()
    file_path = CUSTOM_KEYWORDS_DIR / f"{name}.py"
    if not file_path.exists():
        return None

    spec = importlib.util.spec_from_file_location(f"custom_keywords.{name}", str(file_path))
    if not spec or not spec.loader:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    func = getattr(module, name, None)
    return func


def reload_custom_keywords():
    """Reload all custom keyword modules."""
    ensure_directory()
    to_remove = [key for key in sys.modules if key.startswith("custom_keywords.")]
    for key in to_remove:
        del sys.modules[key]