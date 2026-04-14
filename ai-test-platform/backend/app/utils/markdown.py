"""Markdown 解析工具"""
import re
from typing import List, Tuple


def parse_markdown(content: str) -> dict:
    """
    解析 Markdown 内容

    Args:
        content: Markdown 文本

    Returns:
        {
            "title": str,
            "headings": [{"level": int, "text": str}],
            "paragraphs": [str],
            "code_blocks": [{"language": str, "code": str}],
            "lists": [str],
        }
    """
    lines = content.split("\n")
    result = {
        "title": "",
        "headings": [],
        "paragraphs": [],
        "code_blocks": [],
        "lists": [],
    }

    in_code_block = False
    code_block_content = []
    code_block_lang = ""

    for line in lines:
        if line.startswith("```"):
            if in_code_block:
                # 结束代码块
                result["code_blocks"].append({
                    "language": code_block_lang,
                    "code": "\n".join(code_block_content)
                })
                code_block_content = []
                code_block_lang = ""
                in_code_block = False
            else:
                # 开始代码块
                in_code_block = True
                code_block_lang = line[3:].strip()
        elif in_code_block:
            code_block_content.append(line)
        elif line.startswith("#"):
            # 标题
            match = re.match(r"^(#{1,6})\s+(.+)", line)
            if match:
                level = len(match.group(1))
                text = match.group(2)
                if level == 1 and not result["title"]:
                    result["title"] = text
                result["headings"].append({"level": level, "text": text})
        elif line.strip().startswith(("- ", "* ", "+ ")):
            result["lists"].append(line.strip()[2:])
        elif line.strip() and not in_code_block:
            result["paragraphs"].append(line.strip())

    return result


def extract_code_blocks(content: str) -> List[Tuple[str, str]]:
    """
    提取 Markdown 中的代码块

    Args:
        content: Markdown 文本

    Returns:
        [(语言, 代码), ...]
    """
    pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)
    return [(lang or "text", code.strip()) for lang, code in matches]


def extract_test_hints(content: str) -> List[str]:
    """
    从 Markdown 中提取测试提示

    查找包含 "test", "Test", "test case", "测试" 等关键词的段落
    """
    hints = []
    parsed = parse_markdown(content)

    for para in parsed["paragraphs"]:
        lower = para.lower()
        if any(keyword in lower for keyword in ["test", "测试", "验证", "检查", "assert"]):
            hints.append(para)

    return hints
