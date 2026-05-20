from __future__ import annotations


class ConversationMemory:
    """多轮对话记忆：保存用户原始问题与助手回复，供 LLM 与检索上下文使用。"""

    def __init__(self, max_turns: int = 10) -> None:
        self.max_turns = max(1, max_turns)
        self._turns: list[tuple[str, str]] = []

    @property
    def turn_count(self) -> int:
        return len(self._turns)

    def has_history(self) -> bool:
        return bool(self._turns)

    def add_turn(self, user: str, assistant: str) -> None:
        self._turns.append((user.strip(), assistant.strip()))
        if len(self._turns) > self.max_turns:
            self._turns = self._turns[-self.max_turns :]

    def clear(self) -> None:
        self._turns.clear()

    def get_chat_messages(self) -> list[dict[str, str]]:
        """返回供 LLM 使用的历史消息（不含 system 与当前轮）。"""
        messages: list[dict[str, str]] = []
        for user, assistant in self._turns:
            messages.append({"role": "user", "content": user})
            messages.append({"role": "assistant", "content": assistant})
        return messages

    def build_contextual_query(self, question: str, context_turns: int = 2) -> str:
        """将近期对话拼入检索/意图判断用的查询，便于理解指代与省略。"""
        if not self._turns:
            return question
        recent = self._turns[-context_turns:]
        lines: list[str] = []
        for user, assistant in recent:
            lines.append(f"用户：{user}")
            summary = assistant if len(assistant) <= 300 else assistant[:300] + "…"
            lines.append(f"助手：{summary}")
        lines.append(f"用户：{question}")
        return "\n".join(lines)
