# Prodigal Task – AI-Powered Knowledge Retrieval

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
## 🛠️ Tech Stack

The project is built using a combination of Python-based libraries and frameworks for data processing, embeddings, language modeling, and web interface development.

---

### 🧠 Backend

- **Python**: Core programming language for data processing and application logic.
- **LangChain**: Framework for building applications with language models, used for document retrieval and question-answering pipelines.
  - `langchain_core`: Provides core components like `PromptTemplate` for custom prompts.
  - `langchain_community`: Includes utilities like `HuggingFaceEmbeddings`, `FAISS`, and `HuggingFacePipeline` for embeddings, vector storage, and LLM integration.
- **RetrievalQA**: Chain for retrieval-augmented question answering.
- **Transformers (Hugging Face)**: Library for loading and running pre-trained language models and tokenizers.
  - `AutoTokenizer` and `AutoModelForCausalLM`: Used to load the `microsoft/phi-2` model for local inference.
  - `pipeline`: Simplifies text generation tasks with pre-configured settings.
- **FAISS**: Efficient vector database for storing and retrieving document embeddings, used for similarity search.
- **HuggingFaceEmbeddings**: Generates embeddings for text using the `BAAI/bge-small-en-v1.5` model, enabling semantic search.
- **CSV Processing**: Built-in Python `csv` module for reading structured data from `output.csv`.

---

### 🌐 Frontend

- **Streamlit**: Python framework for creating an interactive web interface.
  - Features a responsive UI with custom CSS for a black-and-orange theme, chat history display, and user input handling.
  - Supports dynamic components like text inputs, buttons, spinners, and containers for a seamless user experience.

---

### 🔤 Language Model

- **Microsoft Phi-2**: A lightweight, efficient language model (`microsoft/phi-2`) used for local text generation.
  - Configured with mixed precision (`torch_dtype="auto"`) and automatic device mapping (`device_map="auto"`) for optimized performance.
  - **Text generation pipeline parameters**:
    - `max_new_tokens=512`: Limits response length.
    - `temperature=0.1`: Ensures factual and deterministic outputs.
    - `top_p=0.95`: Controls diversity of generated text.
    - `repetition_penalty=1.15`: Reduces repetitive responses.

---

### 🗃️ Data Storage

- **Vector Store**: FAISS-based vector database (`vectorstore/db_faiss`) for storing document embeddings.
- **Input Data**: CSV file (`output.csv`) containing structured data about government schemes, processed row-wise into `Document` objects.
"""

## Features

- Extracts and preprocesses raw CSV
- Embeds text for efficient semantic search
- Integrates LLM (e.g., microsoft/phi-2 and BAAI/bge-small-en-v1.5) for question answering
- Uses FAISS as a fast, scalable vector store
- User-friendly interface for querying in plain English

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/SunnyKumar28/prodigal_task
cd prodigal_task

```
### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

```
### 3. Install Dependencies:

```bash
pip install -r requirements.txt

```
### 4. Run the Streamlit App:

```bash
streamlit run app.py

```
### Project Structure
``` plaintext
Scheme_QA_BOT_Using_RAG
  ├── app.py                # Streamlit application script
  ├── data_processing.py    # Script for CSV processing and vector store creation
  ├── output.csv            # Input CSV file with government scheme data
  ├── vectorstore/          # Directory for FAISS vector store
  │   └── db_faiss/
  ├── requirements.txt      # Python dependencies
└── README.md             # This file

```


