"""英雄联盟智能助手 — 交互入口。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent.assistant import LoLAssistant
from utils.logger import setup_logger


def main() -> None:
    logger = setup_logger()
    print("LOL Game Agent 已启动。输入问题，空行或 quit 退出。\n")
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

        try:
            answer = assistant.answer(question)
            print(f"\n助手: {answer}\n")
        except Exception as e:
            logger.exception("回答失败")
            print(f"\n助手: 出错了 — {e}\n")


if __name__ == "__main__":
    main()
