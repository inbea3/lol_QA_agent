from __future__ import annotations

from openai import OpenAI

from agent.router import Intent, classify_intent
from config.settings import settings
from mcp_tools.time_client import call_time_mcp
from mcp_tools.wiki_client import call_wiki_mcp
from rag.retriever import RAGRetriever
from utils.logger import setup_logger

SYSTEM_PROMPT = """你是英雄联盟智能助手，面向玩家的实战咨询。
请基于提供的知识库上下文与工具结果作答，准确、简洁、可执行。
若知识库无覆盖，请明确说明并给出合理建议，不要编造数值。"""


class LoLAssistant:
    def __init__(self) -> None:
        self.retriever = RAGRetriever()
        self.client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)
        self.logger = setup_logger()

    def answer(self, question: str) -> str:
        intent = classify_intent(question)
        self.logger.info("intent=%s question=%s", intent.value, question)

        tool_context = ""
        if intent == Intent.KNOWLEDGE:
            chunks = self.retriever.search(question)
            tool_context = self.retriever.format_context(chunks)
            self.logger.info("rag_hits=%d", len(chunks))
        elif intent == Intent.TIME:
            tool_context = call_time_mcp(question)
        else:
            chunks = self.retriever.search(question)
            rag_ctx = self.retriever.format_context(chunks)
            wiki_ctx = call_wiki_mcp(question)
            tool_context = f"【本地知识库】\n{rag_ctx}\n\n【百科检索】\n{wiki_ctx}"

        user_content = f"用户问题：{question}\n\n参考资料：\n{tool_context}"
        response = self.client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""
