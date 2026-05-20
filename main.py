"""英雄联盟智能助手 — 交互入口。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent.assistant import LoLAssistant
from utils.logger import setup_logger

_CLEAR_COMMANDS = {"clear", "reset", "清空", "清除", "新对话"}


def main() -> None:
    logger = setup_logger()
    print("LOL Game Agent 已启动。支持多轮对话记忆。")
    print("输入 clear / 清空 可重置对话；空行或 quit 退出。\n")
    assistant = LoLAssistant()

    while True:
        try:
            question = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break

        if not question or question.lower() in {"quit", "exit", "q"}:
            print("再见。")
            break

        if question.lower() in _CLEAR_COMMANDS:
            assistant.clear_memory()
            print("助手: 已清空对话记忆，可以开始新话题。\n")
            continue

        try:
            answer = assistant.answer(question)
            print(f"\n助手: {answer}\n")
        except Exception as e:
            logger.exception("回答失败")
            print(f"\n助手: 出错了 — {e}\n")


if __name__ == "__main__":
    main()
