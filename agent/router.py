from __future__ import annotations

import re
from enum import Enum


class Intent(str, Enum):
    KNOWLEDGE = "knowledge"
    TIME = "time"
    WIKI = "wiki"


_TIME_PATTERNS = [
    r"倒计时|刷新|多久|几分钟|几秒|CD|冷却",
    r"什么时候|何时|几点|时长|对局时间|游戏时间",
    r"小龙|大龙|先锋|野怪|河道蟹",
]

_WIKI_PATTERNS = [
    r"最新|新闻|赛事|版本|改动|补丁|LPL|世界赛",
    r"外服|测试服|实时|今天|最近",
    r"百科|背景故事|选手|战队",
]


def classify_intent(question: str) -> Intent:
    text = question.strip()
    for pat in _TIME_PATTERNS:
        if re.search(pat, text, re.I):
            return Intent.TIME
    for pat in _WIKI_PATTERNS:
        if re.search(pat, text, re.I):
            return Intent.WIKI
    return Intent.KNOWLEDGE
