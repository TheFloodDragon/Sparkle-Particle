"""
SNBT (Stringified Named Binary Tag) 序列化与反序列化工具。
用于 Minecraft 1.20.5+ 粒子选项的编解码。

遵循 Minecraft Wiki SNBT 格式规范：
- 支持单引号和双引号字符串，含完整转义序列
- 非引号值仅在有类型后缀时解析为数值，无后缀时视为字符串
- 数组类型 [B;...] [I;...] [L;...]
- 列表与复合标签允许结尾逗号
"""

# ============================================================
#  序列化（Python → SNBT）
# ============================================================


def to_snbt(value) -> str:
    """将 Python 值递归转为 SNBT 字符串。布尔转字节，浮点精确保存带 d 后缀。"""
    if isinstance(value, bool):
        return "1b" if value else "0b"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value) + "d"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(to_snbt(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{to_snbt(v)}" for k, v in value.items()) + "}"
    return str(value)



# ============================================================
#  反序列化（SNBT → Python）
# ============================================================


def from_snbt(text: str):
    """将 SNBT 字符串解析为 Python 值。"""
    return _SNBTParser(text).parse()


class _SNBTParser:
    """SNBT 递归下降解析器。"""

    _ESCAPE_MAP = {
        'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r',
        's': ' ',  't': '\t', '\\': '\\', "'": "'", '"': '"',
    }

    _UNQUOTED_CHARS = set(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789._+-"
    )

    _FLOAT_SUFFIX = set('fFdD')
    _INT_SUFFIX = set('bBsSiIlL')
    _TWO_CHAR_FIRST = set('sSuU')
    _TWO_CHAR_SECOND = set('bBsSiIlL')

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def _peek(self):
        return self.text[self.pos] if self.pos < len(self.text) else None

    def _char_at(self, offset):
        p = self.pos + offset
        return self.text[p] if p < len(self.text) else None

    def _advance(self):
        ch = self.text[self.pos]
        self.pos += 1
        return ch

    def _skip_ws(self):
        while self.pos < len(self.text) and self.text[self.pos] in " \t\n\r":
            self.pos += 1

    # ----------------------------------------------------------
    #  入口
    # ----------------------------------------------------------

    def parse(self):
        self._skip_ws()
        result = self._parse_value()
        self._skip_ws()
        return result

    # ----------------------------------------------------------
    #  值
    # ----------------------------------------------------------

    def _parse_value(self):
        self._skip_ws()
        ch = self._peek()
        if ch is None:
            raise ValueError("SNBT: 意外的输入结束")
        if ch == "{":
            return self._parse_dict()
        if ch == "[":
            return self._parse_list_or_array()
        if ch in "\"'":
            return self._parse_string(ch)
        # 非引号值：读取完整标记后按后缀识别类型
        return self._parse_unquoted_value()

    # ----------------------------------------------------------
    #  字符串
    # ----------------------------------------------------------

    def _parse_string(self, quote):
        """解析引号字符串（双引号或单引号），支持完整转义序列。"""
        self._advance()  # 跳过开头引号
        parts = []
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == quote:
                self._advance()
                return "".join(parts)
            if ch == "\\":
                self._advance()
                parts.append(self._parse_escape())
            else:
                parts.append(self._advance())
        raise ValueError("SNBT: 字符串未闭合")

    def _parse_escape(self):
        """解析转义序列。"""
        ch = self._advance()
        if ch in self._ESCAPE_MAP:
            return self._ESCAPE_MAP[ch]
        if ch == 'x':
            h = self.text[self.pos:self.pos + 2]
            self.pos += 2
            return chr(int(h, 16))
        if ch == 'u':
            h = self.text[self.pos:self.pos + 4]
            self.pos += 4
            return chr(int(h, 16))
        if ch == 'U':
            h = self.text[self.pos:self.pos + 8]
            self.pos += 8
            return chr(int(h, 16))
        if ch == 'N' and self._peek() == '{':
            self._advance()  # {
            start = self.pos
            while self.pos < len(self.text) and self.text[self.pos] != '}':
                self.pos += 1
            name = self.text[start:self.pos]
            self._advance()  # }
            import unicodedata
            return unicodedata.lookup(name)
        return ch

    # ----------------------------------------------------------
    #  非引号值（后缀识别）
    # ----------------------------------------------------------

    def _parse_unquoted_value(self):
        """
        解析非引号值：读取完整标记，仅识别到后缀时解析为数值，
        否则回退为字符串。
        """
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] in self._UNQUOTED_CHARS:
            self.pos += 1
        token = self.text[start:self.pos]
        if not token:
            raise ValueError(f"SNBT: 非法字符 '{self.text[self.pos]}' 在位置 {self.pos}")
        return self._resolve_token(token)

    @staticmethod
    def _try_int(s):
        """尝试将字符串解析为整数（十进制、0x 十六进制、0b 二进制）。"""
        if not s:
            return None
        sign = 1
        t = s
        if t[0] == '-':
            sign = -1
            t = t[1:]
        elif t[0] == '+':
            t = t[1:]
        if not t:
            return None
        if len(t) > 2 and t[0] == '0' and t[1] in 'xX':
            try:
                return sign * int(t[2:], 16)
            except ValueError:
                return None
        if len(t) > 2 and t[0] == '0' and t[1] in 'bB':
            try:
                return sign * int(t[2:], 2)
            except ValueError:
                return None
        try:
            return int(s)
        except ValueError:
            return None

    @staticmethod
    def _try_float(s):
        """尝试将字符串解析为浮点数。"""
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    @classmethod
    def _resolve_token(cls, token):
        """
        将非引号标记解析为类型化值。
        仅在识别到类型后缀时解析为数值，无后缀时回退为字符串。
        优先级：两字符后缀 → 单字符浮点后缀 → 单字符整数后缀 → 字符串。
        """
        clean = token.replace('_', '')

        # 两字符后缀：sb, ub, ss, us, si, ui, sl, ul（大小写组合）
        if len(clean) > 2 and clean[-2] in cls._TWO_CHAR_FIRST and clean[-1] in cls._TWO_CHAR_SECOND:
            v = cls._try_int(clean[:-2])
            if v is not None:
                return v

        # 单字符浮点后缀：f, F, d, D
        if len(clean) > 1 and clean[-1] in cls._FLOAT_SUFFIX:
            v = cls._try_float(clean[:-1])
            if v is not None:
                return v

        # 单字符整数后缀：b, B, s, S, i, I, l, L
        if len(clean) > 1 and clean[-1] in cls._INT_SUFFIX:
            v = cls._try_int(clean[:-1])
            if v is not None:
                return v

        # 无后缀：回退为字符串
        return token

    # ----------------------------------------------------------
    #  列表 / 数组
    # ----------------------------------------------------------

    def _parse_list_or_array(self):
        """解析列表或类型化数组（[B;...] [I;...] [L;...]）。"""
        self._advance()  # [
        self._skip_ws()
        # 类型化数组检测
        if (self._peek() is not None
                and self._peek() in 'BILbil'
                and self._char_at(1) == ';'):
            self.pos += 2  # 跳过 B; / I; / L;
            return self._parse_items(']', as_int=True)
        return self._parse_items(']')

    def _parse_items(self, close, as_int=False):
        """解析列表/数组元素，支持结尾逗号。"""
        result = []
        self._skip_ws()
        if self._peek() == close:
            self._advance()
            return result
        result.append(self._parse_value())
        while True:
            self._skip_ws()
            if self._peek() == close:
                self._advance()
                break
            if self._peek() == ',':
                self._advance()
                self._skip_ws()
                if self._peek() == close:  # 结尾逗号
                    self._advance()
                    break
            result.append(self._parse_value())
        if as_int:
            return [int(v) for v in result]
        return result

    # ----------------------------------------------------------
    #  复合标签
    # ----------------------------------------------------------

    def _parse_dict(self):
        """解析复合标签，支持结尾逗号和引号/无引号键。"""
        self._advance()  # {
        result = {}
        self._skip_ws()
        if self._peek() == '}':
            self._advance()
            return result
        k, v = self._parse_kv()
        result[k] = v
        while True:
            self._skip_ws()
            if self._peek() == '}':
                self._advance()
                break
            if self._peek() == ',':
                self._advance()
                self._skip_ws()
                if self._peek() == '}':  # 结尾逗号
                    self._advance()
                    break
            k, v = self._parse_kv()
            result[k] = v
        return result

    def _parse_kv(self):
        """解析复合标签的键值对。"""
        self._skip_ws()
        # 键：双引号、单引号、或无引号
        if self._peek() in "\"'":
            key = self._parse_string(self._peek())
        else:
            start = self.pos
            while self.pos < len(self.text) and self.text[self.pos] not in ":,} \t\n\r":
                self.pos += 1
            key = self.text[start:self.pos].strip()
        self._skip_ws()
        self._advance()  # :
        val = self._parse_value()
        return key, val
