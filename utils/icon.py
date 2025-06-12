"""图标相关的工具"""

import os
import tempfile
from typing import overload, Literal, Optional
from utils.general import Path

POSSIBLE_ICON_EXT = ["png", "ico", "svg", "jpg"]

def create_default_icon() -> Path:
    """不依赖其他文件的情况下，创建一个默认图标，返回图标路径"""
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (64, 64), color=(70, 130, 180))
    d = ImageDraw.Draw(img)
    d.text((10, 25), "AI", fill=(255, 255, 255))
    temp_icon = os.path.join(
        tempfile.gettempdir(), "assistant_temp_icon.ico")
    img.save(temp_icon)
    return temp_icon

@overload
def get_icon(base_name: str, allow_create: Literal[True] = True) -> Path:
    ...

@overload
def get_icon(base_name: str, allow_create: Literal[False]) -> Optional[Path]:
    ...

def get_icon(base_name: str, allow_create: bool = True) -> Optional[Path]:
    """根据一个名字，获取可能为图标的路径"""
    for ext in POSSIBLE_ICON_EXT:
        icon_path = f"{base_name}.{ext}"
        if os.path.exists(icon_path):
            return icon_path
    
    if allow_create:
        return create_default_icon()
    else:
        return None

