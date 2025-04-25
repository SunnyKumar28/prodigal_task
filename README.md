# Prodigal Task – AI-Powered Knowledge Retrieval Pipeline

Welcome to the **Prodigal Task**, an end-to-end pipeline that extracts knowledge from raw documents and enables semantic search and question-answering using advanced embedding techniques and LLMs. This system transforms unstructured CSV into a powerful knowledge base you can query in natural language.

---
## 🚀 Demo

[Click here to watch the demo video 📺](https://drive.google.com/drive/folders/15ldYt7tK8BVXo7LfVHBmjYPB2LgJt1my?usp=drive_link)
)

## Flowchart Overview

The system operates in **three distinct phases**:

### Phase 1 – Document Processing & Embedding

Raw CSV files are:
1. Parsed into structured chunks of text.
2. Embedded using a vectorizer (e.g., Sentence Transformers).
3. Stored in a vector store (such as FAISS).

![Phase 1 Flowchart](https://github.com/user-attachments/assets/388b43c6-3df1-422b-b882-0abb620da909)

---

### Phase 2 – Semantic Search & LLM Integration

1. User input is converted to question embeddings.
2. Embeddings are compared to the knowledge base for semantic search.
3. Top-k matching results are passed to the LLM for contextual answering.

---

### Phase 3 – User Interaction

The user can:
- Ask natural language questions.
- Receive detailed, context-aware responses powered by the LLM.

---

## App Preview

| Start | Ask Questions | Get Answers |
|-------------|----------------|-------------|
| ![Upload](https://github.com/user-attachments/assets/9bd80079-28b5-43fe-b9b2-4703d3e302e8) | ![Question](https://github.com/user-attachments/assets/248b2ce4-3e07-45b7-a9e0-78a4d86cdd2b) | ![Answer](https://github.com/user-attachments/assets/4df2585a-7ded-4e95-85e4-a8cd2f7ec9d6) |

---

## Features

- Extracts and preprocesses raw CSV
- Embeds text for efficient semantic search
- Integrates LLM (e.g., OpenAI GPT or similar) for question answering
- Uses FAISS as a fast, scalable vector store
- User-friendly interface for querying in plain English

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/prodigal_task.git
cd prodigal_task
