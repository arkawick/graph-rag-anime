"""Streamlit web UI for Neo4j Graph RAG."""

import streamlit as st
from src.graph import Neo4jClient
from src.embeddings import Embedder
from src.rag import HybridRetriever, AnswerGenerator, RAGEngine

# Page config
st.set_page_config(
    page_title="Neo4j Graph RAG",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if "rag_engine" not in st.session_state:
    with st.spinner("Initializing RAG system..."):
        try:
            neo4j = Neo4jClient()
            embedder = Embedder()
            retriever = HybridRetriever(neo4j, embedder)
            generator = AnswerGenerator()
            st.session_state.rag_engine = RAGEngine(retriever, generator)
            st.session_state.neo4j = neo4j
            st.success("✓ RAG system initialized!")
        except Exception as e:
            st.error(f"Failed to initialize: {e}")
            st.stop()

# Header
st.title("🔍 Neo4j Graph RAG")
st.markdown("Ask questions about your documents using AI-powered knowledge graph retrieval.")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    top_k = st.slider("Number of chunks to retrieve", 1, 20, 5)
    use_graph = st.checkbox("Use graph expansion", value=True)

    st.divider()

    st.header("📊 Statistics")
    if st.button("Refresh Stats"):
        try:
            stats = st.session_state.neo4j.get_statistics()
            st.metric("Documents", stats["document_count"])
            st.metric("Chunks", stats["chunk_count"])
            st.metric("Entities", stats["entity_count"])
            st.metric("Relationships", stats["relationship_count"])
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    st.header("🔧 Actions")
    if st.button("Clear Database", type="secondary"):
        if st.confirm("Are you sure?"):
            st.session_state.neo4j.clear_database()
            st.success("Database cleared!")
            st.rerun()

# Main content
st.header("💬 Ask a Question")

# Query input
question = st.text_input(
    "Enter your question:",
    placeholder="What does the documentation say about...?"
)

if st.button("Search", type="primary") or question:
    if question:
        with st.spinner("Searching knowledge graph..."):
            try:
                # Query the system
                result = st.session_state.rag_engine.query(
                    question=question,
                    top_k=top_k,
                    use_graph=use_graph,
                    verbose=False
                )

                # Display answer
                st.subheader("📝 Answer")
                st.markdown(result["answer"])

                # Display sources
                if result.get("sources"):
                    st.subheader("📚 Sources")
                    for i, source in enumerate(result["sources"], 1):
                        with st.expander(f"Source {i}: {source['source']}"):
                            st.write(f"Relevance: {source['relevance']:.2%}")

                # Display metadata
                with st.expander("ℹ️ Query Details"):
                    st.json({
                        "chunks_retrieved": result["num_chunks"],
                        "top_k": top_k,
                        "graph_expansion": use_graph
                    })

            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.info("Please enter a question above.")

# Example queries
st.divider()
st.subheader("💡 Example Questions")

example_queries = [
    "What is the main topic of the documents?",
    "Summarize the key points",
    "What technologies are mentioned?",
    "Explain the methodology"
]

cols = st.columns(2)
for i, query in enumerate(example_queries):
    col = cols[i % 2]
    if col.button(query, key=f"example_{i}"):
        st.rerun()

# Footer
st.divider()
st.caption("Powered by Neo4j, LangChain, and OpenAI")
