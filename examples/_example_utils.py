"""示例脚本的公共辅助函数。"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "output"


def bootstrap_repo_path() -> None:
    """确保示例脚本可以直接导入仓库根目录下的 sparkle 包。"""
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
