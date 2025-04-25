
import csv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Step 1: Load CSV file row-wise
DATA_PATH = "output.csv"
def load_csv_file(data_path):
    documents = []
    with open(data_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row_num, row in enumerate(csv_reader, start=1):
            # Format row content as a structured string (e.g., "Column1: value1, Column2: value2")
            content = ", ".join(f"{key}: {value}" for key, value in row.items())
            # Create a Document object with the content and metadata
            doc = Document(
                page_content=content,
                metadata={"source": data_path, "row_number": row_num, "row_data": row}
            )
            documents.append(doc)
    return documents

# Load CSV data
documents = load_csv_file(data_path=DATA_PATH)
print("Number of CSV rows processed (documents): ", len(documents))

# Step 2: Display a sample of chunked data
def display_sample_chunks(documents, num_samples=3):
    print("\nSample of Chunked Data:")
    print("-----------------------")
    # Limit to the first few documents or the total number available
    for i, doc in enumerate(documents[:min(num_samples, len(documents))], 1):
        print(f"Chunk {i}:")
        print(f"Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}")
        print("-----------------------")

# Display up to 3 sample chunks
display_sample_chunks(documents, num_samples=3)

# Step 3: Create Vector Embeddings
def get_embedding_model():
    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    return embedding_model

embedding_model = get_embedding_model()

# Step 4: Store embeddings in FAISS
DB_FAISS_PATH = "vectorstore/db_faiss"
db = FAISS.from_documents(documents, embedding_model)
db.save_local(DB_FAISS_PATH)
print(f"Embeddings saved to {DB_FAISS_PATH}")