import streamlit as st
import httpx

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="RAG Playground",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Basav's RAG Playground")
st.markdown(
    ":orange-badge[⚠️ Work in Progress]"
)

documents_ingested_tab, upload_documents_tab, chat_tab = st.tabs([
    "📄 Documents Ingested",
    "📄 Upload Documents",
    "💬 Query",
])

with documents_ingested_tab:
    st.subheader("Documents Ingested")


with upload_documents_tab:
    # Create your columns normally
    col1, _ = st.columns([6, 6])
    with col1:
        st.subheader("Upload Document")

        client_doc_id = st.text_input("Enter ID for the Document", key="client_doc_id")
        force_reingest = st.toggle("Force Re-ingest", key="force_reingest")

        uploaded_file = st.file_uploader(
            "Select a document",
            type=["pdf"],
        )

        if uploaded_file and st.button("Ingest Document"):
            with st.spinner("Ingesting document..."):
                files = {
                    "upload_file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type,
                    )
                }
                data={
                    "client_doc_id": client_doc_id,
                    "force_reingest": force_reingest
                }

                response = httpx.post(
                    f"{API_BASE_URL}/documents/ingest",
                    headers={"accept": "application/json"},
                    files=files,
                    timeout=120,
                    data=data,
                )

                if response.is_success:
                    st.success("Document ingested successfully")
                    st.json(response.json())
                else:
                    st.error(
                        f"Ingestion failed: {response.text}"
                    )


with chat_tab:
    # Create your columns normally
    col1, _ = st.columns([6, 6])
    with col1:
        st.subheader("Ask your documents")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        ret_client_doc_id = st.text_input("Enter ID for the Document", key="retrieve_client_doc_id")
        question = st.chat_input(
            "Ask a question about your documents"
        )

        if question:
            st.session_state.messages.append({
                "role": "user",
                "content": question,
            })

            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Searching documents..."):
                    response = httpx.post(
                        f"{API_BASE_URL}/documents/retrieve_context",
                        json={
                            "query": question,
                            "top_k": 5,
                            "client_doc_id": ret_client_doc_id
                        },
                        timeout=120,
                    )

                    if response.is_success:
                        result = response.json()

                        answer = result["total_chunks_retrieved"]

                        st.markdown(answer)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                        })

                        # with st.expander("Retrieved Context"):
                        #     for source in result.get("contexts", []):
                        #         st.markdown(
                        #             f"**{source['document_name']}**"
                        #         )
                        #         st.write(source["content"])
                    else:
                        st.error(response.text)
