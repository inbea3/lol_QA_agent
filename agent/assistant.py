from __future__ import annotations

from openai import OpenAI

from agent.memory import ConversationMemory
from agent.router import Intent, classify_intent
from config.settings import settings
from mcp_tools.time_client import call_time_mcp
from mcp_tools.wiki_client import call_wiki_mcp
from rag.retriever import RAGRetriever
from utils.logger import setup_logger

SYSTEM_PROMPT = """你是英雄联盟智能助手，面向玩家的实战咨询。
请基于提供的知识库上下文与工具结果作答，准确、简洁、可执行。
若知识库无覆盖，请明确说明并给出合理建议，不要编造数值。
多轮对话中，请结合上文理解用户的指代（如「他」「这个」「还有呢」），保持话题连贯。"""


class LoLAssistant:
    def __init__(self) -> None:
        self.retriever = RAGRetriever()
        self.client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)
        self.logger = setup_logger()
        self.memory = ConversationMemory(max_turns=settings.memory_max_turns)

    def clear_memory(self) -> None:
        self.memory.clear()
        self.logger.info("conversation memory cleared")

    def answer(self, question: str) -> str:
        search_query = self.memory.build_contextual_query(question)
        intent = classify_intent(search_query)
        self.logger.info(
            "intent=%s question=%s turns=%d",
            intent.value,
            question,
            self.memory.turn_count,
        )

        tool_context = ""
        if intent == Intent.KNOWLEDGE:
            chunks = self.retriever.search(search_query)
            tool_context = self.retriever.format_context(chunks)
            self.logger.info("rag_hits=%d", len(chunks))
        elif intent == Intent.TIME:
            tool_context = call_time_mcp(search_query)
        else:
            chunks = self.retriever.search(search_query)
            rag_ctx = self.retriever.format_context(chunks)
            wiki_ctx = call_wiki_mcp(search_query)
            tool_context = f"【本地知识库】\n{rag_ctx}\n\n【百科检索】\n{wiki_ctx}"

        user_content = f"用户问题：{question}\n\n参考资料：\n{tool_context}"
        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self.memory.get_chat_messages(),
            {"role": "user", "content": user_content},
        ]
        response = self.client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            temperature=0.3,
        )
        answer = response.choices[0].message.content or ""
        self.memory.add_turn(question, answer)
        return answer
