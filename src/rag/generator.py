"""Answer generation using LLM."""

import os
from typing import List, Dict, Any
from rich.console import Console
from ..config import config

console = Console()


class AnswerGenerator:
    """Generate answers using LLM with retrieved context."""

    def __init__(self, provider: str = None, model: str = None):
        self.provider = provider or config.llm.provider
        self.model = model or config.llm.model

        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM based on provider."""
        console.print(f"[yellow]Initializing LLM ({self.provider}/{self.model})...[/yellow]")

        if self.provider == "openai":
            from langchain_openai import ChatOpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")

            self.llm = ChatOpenAI(
                model=self.model,
                temperature=config.llm.temperature,
                max_tokens=config.llm.max_tokens,
                openai_api_key=api_key
            )

        elif self.provider == "ollama":
            from langchain_community.llms import Ollama
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

            self.llm = Ollama(
                model=self.model or "llama2",
                base_url=base_url
            )

        elif self.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")

            self.llm = ChatAnthropic(
                model=self.model or "claude-3-sonnet-20240229",
                temperature=config.llm.temperature,
                max_tokens=config.llm.max_tokens,
                anthropic_api_key=api_key
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        console.print(f"[green]✓ LLM initialized[/green]")

    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Generate an answer using retrieved context.

        Args:
            query: User query
            context_chunks: List of retrieved chunks
            include_sources: Whether to include source citations

        Returns:
            Dictionary with answer and sources
        """
        # Build context from chunks
        context = self._build_context(context_chunks)

        # Create prompt
        prompt = self._create_prompt(query, context)

        # Generate answer
        if self.provider in ["openai", "anthropic"]:
            from langchain.schema import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            answer = response.content
        else:  # ollama
            answer = self.llm.invoke(prompt)

        # Prepare result
        result = {
            "answer": answer,
            "query": query
        }

        if include_sources:
            result["sources"] = self._extract_sources(context_chunks)
            result["num_chunks"] = len(context_chunks)

        return result

    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("text", "")
            source = chunk.get("source", "unknown")
            score = chunk.get("score", 0.0)

            context_parts.append(
                f"[Document {i}] (Source: {source}, Relevance: {score:.2f})\n{text}"
            )

        return "\n\n---\n\n".join(context_parts)

    def _create_prompt(self, query: str, context: str) -> str:
        """Create prompt for the LLM."""
        prompt = f"""You are a helpful assistant that answers questions based on the provided context.

Context:
{context}

Question: {query}

Instructions:
1. Answer the question based ONLY on the information provided in the context above
2. If the context doesn't contain enough information to answer, say so
3. Cite the relevant document numbers in your answer (e.g., "According to Document 1...")
4. Be concise and accurate
5. If multiple documents provide relevant information, synthesize them

Answer:"""

        return prompt

    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract unique sources from chunks."""
        sources = {}

        for chunk in chunks:
            source = chunk.get("source", "unknown")
            if source not in sources:
                sources[source] = {
                    "source": source,
                    "relevance": chunk.get("score", 0.0)
                }

        # Sort by relevance
        return sorted(
            sources.values(),
            key=lambda x: x["relevance"],
            reverse=True
        )
