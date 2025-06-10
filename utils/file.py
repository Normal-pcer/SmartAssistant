"""文件相关实用工具"""

import mimetypes
from utils.general import Path

def is_text(file_path: Path) -> bool:
    mime = mimetypes.guess_type(file_path)[0]
    if mime is None:
        return False
    return "text" in mime
