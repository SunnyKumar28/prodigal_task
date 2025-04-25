# # import os
# # import streamlit as st
# # from langchain_core.prompts import PromptTemplate
# # from langchain.chains import RetrievalQA
# # from langchain_community.embeddings import HuggingFaceEmbeddings
# # from langchain_community.vectorstores import FAISS
# # from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
# # from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline

# # # Set Streamlit page configuration
# # st.set_page_config(page_title="Government Scheme QnA", layout="wide")
# # # Inject custom CSS for styling
# # st.markdown("""
# #     <style>
# #     /* Center the title */
# #     .title {
# #         text-align: center;
# #         font-size: 2.5em;
# #         font-weight: bold;
# #         color: #1E88E5;
# #         margin-bottom: 0.5em
# #         margin-left:10em;
# #     }
# #     /* Style the subtitle/description */
# #     .subtitle {
# #         text-align: center;
# #         font-size: 1.2em;
# #         color: #555555;
# #         margin-bottom: 2em;
# #     }
# #     /* Style the input box */
# #     .stTextInput > div > div > input {
# #         border: 2px solid #1E88E5;
# #         border-radius: 5px;
# #         padding: 10px;
# #         font-size: 1em;
# #     }
# #     /* Style the answer section */
# #     .answer-section {
# #         background-color: #F5F5F5;
# #         padding: 20px;
# #         border-radius: 10px;
# #         margin-top: 20px;
# #         box-shadow: 0 4px 8px rgba(0,0,0,0.1);
# #     }
# #     .answer-section h3 {
# #         color: #ecccf0;
# #         font-size: 1.5em;
# #         margin-bottom: 10px;
# #     }
# #     .answer-section p {
# #         font-size: 1.1em;
# #         color: #333333;
# #     }
# #     </style>
# # """, unsafe_allow_html=True)


# # # Load local LLM
# # @st.cache_resource
# # # def load_local_llm(model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
# # def load_local_llm(model_id="meta-llama/Meta-Llama-3-8B"):
# #     tokenizer = AutoTokenizer.from_pretrained(model_id)
# #     model = AutoModelForCausalLM.from_pretrained(model_id)
    
# #     pipe = pipeline(
# #         "text-generation",
# #         model=model,
# #         tokenizer=tokenizer,
# #         max_new_tokens=512,
# #     )
# #     llm = HuggingFacePipeline(pipeline=pipe)
# #     return llm


# # CUSTOM_PROMPT_TEMPLATE = """ You are an expert at extracting specific information from structured context about government schemes. The context is a comma-separated string containing fields such as: scheme name, ministries/departments, target beneficiaries, eligibility criteria, description & benefits, application process, and tags. Each field is formatted as 'field_name: value'.

# # Your task is to answer the user's question by:





# # Identifying the specific field(s) in the context that directly correspond to the information requested (e.g., 'eligibility criteria' for questions about eligibility, 'application process' for questions about how to apply).



# # Extracting and returning only the value of the relevant field(s), without including other fields or additional commentary.



# # Responding with 'Not available' if the requested information is not present in the context or if no field matches the question.



# # Handling synonyms or paraphrased questions (e.g., 'who can apply' or 'requirements' should map to 'eligibility criteria'; 'how to apply' should map to 'application process').



# # If the question is ambiguous or could map to multiple fields, prioritize the most relevant field based on common sense (e.g., 'what is the scheme about' maps to 'description & benefits').

# # Rules:





# # Answer concisely, using only the text from the relevant field's value.



# # Do not summarize, rephrase, or include information from other fields unless explicitly asked.



# # Do not make up or infer information beyond what is provided in the context.



# # If the question asks for information not associated with a specific field (e.g., 'duration of training'), respond with 'Not available' unless the context explicitly provides it.

# # Context: {context} Question: {question}

# # Answer: """


# # def set_custom_prompt(template):
# #     return PromptTemplate(template=template, input_variables=["context", "question"])

# # # Load vectorstore
# # @st.cache_resource
# # def load_vector_store(path="vectorstore/db_faiss"):
# #     embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
# #     db = FAISS.load_local(path, embedding_model, allow_dangerous_deserialization=True)
# #     return db

# # # Initialize QA Chain
# # @st.cache_resource
# # def load_qa_chain():
# #     llm = load_local_llm()
# #     db = load_vector_store()
# #     qa = RetrievalQA.from_chain_type(
# #         llm=llm,
# #         chain_type="stuff",
# #         retriever=db.as_retriever(search_kwargs={'k': 3}),
# #         return_source_documents=True,
# #         chain_type_kwargs={'prompt': set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
# #     )
# #     return qa

# # # Function to extract text after "Answer:"
# # def extract_answer(response):
# #     if "Answer:" in response:
# #         return response.split("Answer:")[1].strip()
# #     return response.strip()  # Fallback if "Answer:" is not found

# # # Streamlit UI
# # # Centered title using custom CSS class
# # st.markdown('<div class="title">Government Scheme QnA Bot</div>', unsafe_allow_html=True)
# # st.markdown('<div class="subtitle">Ask any question related to Indian government schemes (powered by MyScheme portal data).</div>', unsafe_allow_html=True)

# # # Create a container for the input and output
# # with st.container():
# #     query = st.text_input("Enter your question here", "")

# #     if query:
# #         with st.spinner("Getting answer..."):
# #             qa_chain = load_qa_chain()
# #             result = qa_chain.invoke({'query': query})

# #             # Extract only the answer
# #             final_answer = extract_answer(result["result"])

# #             # Display answer in styled section
# #             st.markdown('<div class="answer-section">', unsafe_allow_html=True)
# #             st.subheader("Answer:")
# #             st.markdown(final_answer)
# #             st.markdown('</div>', unsafe_allow_html=True)




# #  version5
# import os
# import streamlit as st
# from langchain_core.prompts import PromptTemplate
# from langchain.chains import RetrievalQA
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_community.vectorstores import FAISS
# from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
# from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
# import hashlib

# # Simple in-memory user database (for demo purposes; replace with secure storage in production)
# if 'USER_DB' not in st.session_state:
#     st.session_state['USER_DB'] = {
#         "admin": hashlib.sha256("password123".encode()).hexdigest(),
#     }

# # Initialize chat history
# if 'CHAT_HISTORY' not in st.session_state:
#     st.session_state['CHAT_HISTORY'] = []

# # Function to check login
# def check_login(username, password):
#     if username in st.session_state['USER_DB']:
#         hashed_password = hashlib.sha256(password.encode()).hexdigest()
#         return hashed_password == st.session_state['USER_DB'][username]
#     return False

# # Function to add new user
# def add_user(username, password):
#     if username not in st.session_state['USER_DB']:
#         hashed_password = hashlib.sha256(password.encode()).hexdigest()
#         st.session_state['USER_DB'][username] = hashed_password
#         return True
#     return False

# # Set Streamlit page configuration
# st.set_page_config(page_title="Government Scheme QnA", layout="wide")

# # Inject custom CSS for black and orange theme, including chat history styling
# st.markdown("""
#     <style>
#     body {
#         background-color: #1a1a1a;
#         color: #fff;
#     }
#     .title {
#         text-align: center;
#         font-size: 2.5em;
#         font-weight: bold;
#         color: #ff6200;
#         margin-bottom: 0.5em;
#     }
#     .subtitle {
#         text-align: center;
#         font-size: 1.2em;
#         color: #ff6200;
#         margin-bottom: 2em;
#     }
#     .auth-container {
#         max-width: 600px;
#         margin: 0;
#         padding: 20px;
#         color: #fff;
#     }
#     .stTextInput > div > div > input {
#         border: 2px solid #ff6200;
#         border-radius: 5px;
#         padding: 10px;
#         font-size: 1em;
#         background-color: #333;
#         color: #fff;
#         width: 100%;
#     }
#     .stButton>button {
#         background-color: #ff6200;
#         color: #fff;
#         border: none;
#         padding: 10px 20px;
#         border-radius: 5px;
#         font-size: 1em;
#     }
#     .stRadio > label {
#         color: #ff6200;
#         font-size: 1.1em;
#         margin-right: 20px;
#     }
#     .stRadio > div {
#         display: flex;
#         gap: 20px;
#     }
#     .answer-section {
#         background-color: rgba(0, 0, 0, 0.8);
#         padding: 20px;
#         border: 2px solid #ff6200;
#         border-radius: 10px;
#         margin-top: 20px;
#         box-shadow: 0 4px 8px rgba(255, 98, 0, 0.3);
#     }
#     .answer-section h3 {
#         color: #ff6200;
#         font-size: 1.5em;
#         margin-bottom: 10px;
#     }
#     .answer-section p {
#         font-size: 1.1em;
#         color: #fff;
#     }
#     .chat-history {
#         max-height: 400px;
#         overflow-y: auto;
#         margin-bottom: 20px;
#         padding: 10px;
#         border: 1px solid #ff6200;
#         border-radius: 10px;
#         background-color: rgba(0, 0, 0, 0.8);
#     }
#     .chat-message {
#         margin: 10px 0;
#         padding: 10px;
#         border-radius: 5px;
#         max-width: 80%;
#     }
#     .user-message {
#         background-color: #ff6200;
#         color: #fff;
#         margin-left: auto;
#         text-align: right;
#     }
#     .bot-message {
#         background-color: #333;
#         color: #fff;
#         margin-right: auto;
#         text-align: left;
#     }
#     </style>
# """, unsafe_allow_html=True)

# # Initialize session state for login
# if 'LOGGED_IN' not in st.session_state:
#     st.session_state['LOGGED_IN'] = False

# # Login and Signup UI
# if not st.session_state['LOGGED_IN']:
#     st.markdown('<div class="title">Government Scheme QnA</div>', unsafe_allow_html=True)
#     auth_mode = st.radio("", ["Login", "Signup"], horizontal=True)
#     with st.container():
#         st.markdown('<div class="auth-container">', unsafe_allow_html=True)
#         st.subheader(auth_mode)
#         if auth_mode == "Login":
#             username = st.text_input("Username")
#             password = st.text_input("Password", type="password")
#             if st.button("Login"):
#                 if check_login(username, password):
#                     st.session_state['LOGGED_IN'] = True
#                     st.rerun()
#                 else:
#                     st.error("Invalid username or password")
#         else:  # Signup
#             new_username = st.text_input("New Username")
#             new_password = st.text_input("New Password", type="password")
#             confirm_password = st.text_input("Confirm Password", type="password")
#             if st.button("Signup"):
#                 if new_password == confirm_password and new_username:
#                     if add_user(new_username, new_password):
#                         st.success("Account created successfully! Please log in.")
#                     else:
#                         st.error("Username already exists!")
#                 else:
#                     st.error("Passwords do not match or fields are empty!")
#         st.markdown('</div>', unsafe_allow_html=True)
# else:
#     # Logout button Servicio de atención al cliente
#     if st.button("Logout"):
#         st.session_state['LOGGED_IN'] = False
#         st.session_state['CHAT_HISTORY'] = []  # Clear chat history on logout
#         st.rerun()

#     # Load local LLM
#     @st.cache_resource
#     def load_local_llm(model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
#         tokenizer = AutoTokenizer.from_pretrained(model_id)
#         model = AutoModelForCausalLM.from_pretrained(model_id)
        
#         pipe = pipeline(
#             "text-generation",
#             model=model,
#             tokenizer=tokenizer,
#             max_new_tokens=512,
#         )
#         llm = HuggingFacePipeline(pipeline=pipe)
#         return llm

#     CUSTOM_PROMPT_TEMPLATE = """ You are an expert at extracting specific information from structured context about government schemes. The context is a comma-separated string containing fields such as: scheme name, ministries/departments, target beneficiaries, eligibility criteria, description & benefits, application process, and tags. Each field is formatted as 'field_name: value'.

#     Your task is to answer the user's question by:

#     Identifying the specific field(s) in the context that directly correspond to the information requested (e.g., 'eligibility criteria' for questions about eligibility, 'application process' for questions about how to apply).

#     Extracting and returning only the value of the relevant field(s), without including other fields or additional commentary.

#     Responding with 'Not available' if the requested information is not present in the context or if no field matches the question.

#     Handling synonyms or paraphrased questions (e.g., 'who can apply' or 'requirements' should map to 'eligibility criteria'; 'how to apply' should map to 'application process').

#     If the question is ambiguous or could map to multiple fields, prioritize the most relevant field based on common sense (e.g., 'what is the scheme about' maps to 'description & benefits').

#     Rules:

#     Answer concisely, using only the text from the relevant field's value.

#     Do not summarize, rephrase, or include information from other fields unless explicitly asked.

#     Do not make up or infer information beyond what is provided in the context.

#     If the question asks for information not associated with a specific field (e.g., 'duration of training'), respond with 'Not available' unless the context explicitly provides it.

#     Context: {context} Question: {question}

#     Answer: """

#     def set_custom_prompt(template):
#         return PromptTemplate(template=template, input_variables=["context", "question"])

#     # Load vectorstore
#     @st.cache_resource
#     def load_vector_store(path="vectorstore/db_faiss"):
#         embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
#         db = FAISS.load_local(path, embedding_model, allow_dangerous_deserialization=True)
#         return db

#     # Initialize QA Chain
#     @st.cache_resource
#     def load_qa_chain():
#         llm = load_local_llm()
#         db = load_vector_store()
#         qa = RetrievalQA.from_chain_type(
#             llm=llm,
#             chain_type="stuff",
#             retriever=db.as_retriever(search_kwargs={'k': 3}),
#             return_source_documents=True,
#             chain_type_kwargs={'prompt': set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
#         )
#         return qa

#     # Function to extract text after "Answer:"
#     def extract_answer(response):
#         if "Answer:" in response:
#             return response.split("Answer:")[1].strip()
#         return response.strip()  # Fallback if "Answer:" is not found

#     # Streamlit UI for QnA
#     st.markdown('<div class="title">Government Scheme QnA Bot</div>', unsafe_allow_html=True)
#     st.markdown('<div class="subtitle">Ask any question related to Indian government schemes (powered by MyScheme portal data).</div>', unsafe_allow_html=True)

#     # Create a container for the input and output
#     with st.container():
#         # Display chat history
#         st.markdown('<div class="chat-history">', unsafe_allow_html=True)
#         for query, answer in st.session_state['CHAT_HISTORY']:
#             st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {query}</div>', unsafe_allow_html=True)
#             st.markdown(f'<div class="chat-message bot-message"><strong>Bot:</strong> {answer}</div>', unsafe_allow_html=True)
#         st.markdown('</div>', unsafe_allow_html=True)

#         # Query input
#         query = st.text_input("Enter your question here", "")
#         if query:
#             with st.spinner("Getting answer..."):
#                 qa_chain = load_qa_chain()
#                 result = qa_chain.invoke({'query': query})

#                 # Extract only the answer
#                 final_answer = extract_answer(result["result"])

#                 # Append to chat history
#                 st.session_state['CHAT_HISTORY'].append((query, final_answer))

#                 # Display answer in styled section
#                 st.markdown('<div class="answer-section">', unsafe_allow_html=True)
#                 st.subheader("Answer:")
#                 st.markdown(final_answer)
#                 st.markdown('</div>', unsafe_allow_html=True)






# /*using microsoftphi model */

# import os
# import streamlit as st
# from langchain_core.prompts import PromptTemplate
# from langchain.chains import RetrievalQA
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_community.vectorstores import FAISS
# from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
# from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline

# # Set Streamlit page configuration
# st.set_page_config(page_title="Government Scheme QnA", layout="wide")
# # Inject custom CSS for styling
# st.markdown("""
#     <style>
#     /* Center the title */
#     .title {
#         text-align: center;
#         font-size: 2.5em;
#         font-weight: bold;
#         color: #1E88E5;
#         margin-bottom: 0.5em;
#     }
#     /* Style the subtitle/description */
#     .subtitle {
#         text-align: center;
#         font-size: 1.2em;
#         color: #555555;
#         margin-bottom: 2em;
#     }
#     /* Style the input box */
#     .stTextInput > div > div > input {
#         border: 2px solid #1E88E5;
#         border-radius: 5px;
#         padding: 10px;
#         font-size: 1em;
#     }
#     /* Style the answer section */
#     .answer-section {
#         background-color: #F5F5F5;
#         padding: 20px;
#         border-radius: 10px;
#         margin-top: 20px;
#         box-shadow: 0 4px 8px rgba(0,0,0,0.1);
#     }
#     .answer-section h3 {
#         color: #ecccf0;
#         font-size: 1.5em;
#         margin-bottom: 10px;
#     }
#     .answer-section p {
#         font-size: 1.1em;
#         color: #333333;
#     }
#     </style>
# """, unsafe_allow_html=True)


# # Load local LLM
# @st.cache_resource
# def load_local_llm(model_id="microsoft/phi-2"):
#     tokenizer = AutoTokenizer.from_pretrained(model_id)
#     model = AutoModelForCausalLM.from_pretrained(
#         model_id,
#         torch_dtype="auto",  # Use mixed precision
#         device_map="auto",   # Automatically distribute across available GPUs
#         trust_remote_code=True
#     )
    
#     pipe = pipeline(
#         "text-generation",
#         model=model,
#         tokenizer=tokenizer,
#         max_new_tokens=512,
#         temperature=0.1,     # Lower temperature for more factual responses
#         top_p=0.95,
#         repetition_penalty=1.15
#     )
#     llm = HuggingFacePipeline(pipeline=pipe)
#     return llm


# CUSTOM_PROMPT_TEMPLATE = """You are an expert at extracting specific information from structured context about government schemes. The context is a comma-separated string containing fields such as: scheme name, ministries/departments, target beneficiaries, eligibility criteria, description & benefits, application process, and tags. Each field is formatted as 'field_name: value'.

# Your task is to answer the user's question by:

# 1. Identifying the specific field(s) in the context that directly correspond to the information requested (e.g., 'eligibility criteria' for questions about eligibility, 'application process' for questions about how to apply).

# 2. Extracting and returning only the value of the relevant field(s), without including other fields or additional commentary.

# 3. Responding with 'Not available' if the requested information is not present in the context or if no field matches the question.

# 4. Handling synonyms or paraphrased questions (e.g., 'who can apply' or 'requirements' should map to 'eligibility criteria'; 'how to apply' should map to 'application process').

# 5. If the question is ambiguous or could map to multiple fields, prioritize the most relevant field based on common sense (e.g., 'what is the scheme about' maps to 'description & benefits').

# Rules:

# - Answer concisely, using only the text from the relevant field's value.
# - Do not summarize, rephrase, or include information from other fields unless explicitly asked.
# - Do not make up or infer information beyond what is provided in the context.
# - If the question asks for information not associated with a specific field (e.g., 'duration of training'), respond with 'Not available' unless the context explicitly provides it.

# Context: {context} 
# Question: {question}

# Answer: """


# def set_custom_prompt(template):
#     return PromptTemplate(template=template, input_variables=["context", "question"])

# # Load vectorstore
# @st.cache_resource
# def load_vector_store(path="vectorstore/db_faiss"):
#     embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
#     db = FAISS.load_local(path, embedding_model, allow_dangerous_deserialization=True)
#     return db

# # Initialize QA Chain
# @st.cache_resource
# def load_qa_chain():
#     llm = load_local_llm()
#     db = load_vector_store()
#     qa = RetrievalQA.from_chain_type(
#         llm=llm,
#         chain_type="stuff",
#         retriever=db.as_retriever(search_kwargs={'k': 3}),
#         return_source_documents=True,
#         chain_type_kwargs={'prompt': set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
#     )
#     return qa

# # Function to extract text after "Answer:"
# def extract_answer(response):
#     if "Answer:" in response:
#         return response.split("Answer:")[1].strip()
#     return response.strip()  # Fallback if "Answer:" is not found

# # Streamlit UI
# # Centered title using custom CSS class
# st.markdown('<div class="title">Government Scheme QnA Bot</div>', unsafe_allow_html=True)
# st.markdown('<div class="subtitle">Ask any question related to Indian government schemes (powered by MyScheme portal data).</div>', unsafe_allow_html=True)

# # Create a container for the input and output
# with st.container():
#     query = st.text_input("Enter your question here", "")

#     if query:
#         with st.spinner("Getting answer..."):
#             qa_chain = load_qa_chain()
#             result = qa_chain.invoke({'query': query})

#             # Extract only the answer
#             final_answer = extract_answer(result["result"])

#             # Display answer in styled section
#             st.markdown('<div class="answer-section">', unsafe_allow_html=True)
#             st.subheader("Answer:")
#             st.markdown(final_answer)
#             st.markdown('</div>', unsafe_allow_html=True)
            
#             # Optional: Display source documents for debugging
#             # with st.expander("Source Documents"):
#             #     for i, doc in enumerate(result["source_documents"]):
#             #         st.write(f"Document {i+1}:")
#             #         st.write(doc.page_content)
#             #         st.write("---")



import os
import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline

# Initialize session state for chat history if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Set Streamlit page configuration
st.set_page_config(page_title="Government Scheme QnA", layout="wide")
# Inject custom CSS for styling with black and orange theme
st.markdown("""
    <style>
    /* Center the title */
    .title {
        text-align: center;
        font-size: 2.5em;
        font-weight: bold;
        color: #FF8C00; /* Orange color */
        margin-bottom: 0.5em;
    }
    /* Style the subtitle/description */
    .subtitle {
        text-align: center;
        font-size: 1.2em;
        color: #E0E0E0; /* Light gray for better contrast on dark theme */
        margin-bottom: 2em;
    }
    /* Style the input box */
    .stTextInput > div > div > input {
        border: 2px solid #FF8C00; /* Orange border */
        border-radius: 5px;
        padding: 10px;
        font-size: 1em;
        background-color: #333333; /* Dark background */
        color: #FFFFFF; /* White text */
    }
    /* Style the answer section */
    .answer-section {
        background-color: #222222; /* Dark background */
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        box-shadow: 0 4px 8px rgba(255,140,0,0.2); /* Orange glow */
        border-left: 4px solid #FF8C00; /* Orange accent */
    }
    .answer-section h3 {
        color: #FF8C00; /* Orange color */
        font-size: 1.5em;
        margin-bottom: 10px;
    }
    .answer-section p {
        font-size: 1.1em;
        color: #E0E0E0; /* Light gray text */
    }
    /* Chat message styling */
    .user-message {
        background-color: #333333;
        color: #FFFFFF;
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        margin: 10px 0;
        max-width: 80%;
        align-self: flex-end;
        border-left: 3px solid #FF8C00;
    }
    .bot-message {
        background-color: #222222;
        color: #E0E0E0;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0;
        margin: 10px 0;
        max-width: 80%;
        align-self: flex-start;
        border-left: 3px solid #FF8C00;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 20px;
        padding: 10px;
        border-radius: 10px;
        background-color: #121212;
    }
    .message-header {
        font-weight: bold;
        margin-bottom: 5px;
        color: #FF8C00;
    }
    /* Style for the chat history expander */
    .chat-history-header {
        color: #FF8C00;
        font-size: 1.3em;
        font-weight: bold;
        margin-top: 20px;
    }
    /* Overall page background */
    .stApp {
        background-color: #121212; /* Very dark gray, almost black */
    }
    </style>
""", unsafe_allow_html=True)


# Load local LLM
@st.cache_resource
def load_local_llm(model_id="microsoft/phi-2"):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype="auto",  # Use mixed precision
        device_map="auto",   # Automatically distribute across available GPUs
        trust_remote_code=True
    )
    
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=512,
        temperature=0.1,     # Lower temperature for more factual responses
        top_p=0.95,
        repetition_penalty=1.15
    )
    llm = HuggingFacePipeline(pipeline=pipe)
    return llm


CUSTOM_PROMPT_TEMPLATE = """You are an expert at extracting specific information from structured context about government schemes. The context is a comma-separated string containing fields such as: scheme name, ministries/departments, target beneficiaries, eligibility criteria, description & benefits, application process, and tags. Each field is formatted as 'field_name: value'.

Your task is to answer the user's question by:

1. Identifying the specific field(s) in the context that directly correspond to the information requested (e.g., 'eligibility criteria' for questions about eligibility, 'application process' for questions about how to apply).

2. Extracting and returning only the value of the relevant field(s), without including other fields or additional commentary.

3. Responding with 'Not available' if the requested information is not present in the context or if no field matches the question.

4. Handling synonyms or paraphrased questions (e.g., 'who can apply' or 'requirements' should map to 'eligibility criteria'; 'how to apply' should map to 'application process').

5. If the question is ambiguous or could map to multiple fields, prioritize the most relevant field based on common sense (e.g., 'what is the scheme about' maps to 'description & benefits').

Rules:

- Answer concisely, using only the text from the relevant field's value.
- Do not summarize, rephrase, or include information from other fields unless explicitly asked.
- Do not make up or infer information beyond what is provided in the context.
- If the question asks for information not associated with a specific field (e.g., 'duration of training'), respond with 'Not available' unless the context explicitly provides it.

Context: {context} 
Question: {question}

Answer: """


def set_custom_prompt(template):
    return PromptTemplate(template=template, input_variables=["context", "question"])

# Load vectorstore
@st.cache_resource
def load_vector_store(path="vectorstore/db_faiss"):
    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    db = FAISS.load_local(path, embedding_model, allow_dangerous_deserialization=True)
    return db

# Initialize QA Chain
@st.cache_resource
def load_qa_chain():
    llm = load_local_llm()
    db = load_vector_store()
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={'k': 3}),
        return_source_documents=True,
        chain_type_kwargs={'prompt': set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
    )
    return qa

# Function to extract text after "Answer:"
def extract_answer(response):
    if "Answer:" in response:
        return response.split("Answer:")[1].strip()
    return response.strip()  # Fallback if "Answer:" is not found

# Display chat history
def display_chat_history():
    if st.session_state.chat_history:
        st.markdown('<div class="chat-history-header">Chat History</div>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for i, (question, answer) in enumerate(st.session_state.chat_history):
                # User message
                st.markdown(f'<div class="user-message"><div class="message-header">You:</div>{question}</div>', 
                            unsafe_allow_html=True)
                # Bot message
                st.markdown(f'<div class="bot-message"><div class="message-header">Bot:</div>{answer}</div>', 
                            unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
# Function to clear chat history
def clear_history():
    st.session_state.chat_history = []

# Streamlit UI
# Centered title using custom CSS class
st.markdown('<div class="title">Government Scheme QnA Bot</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask any question related to Indian government schemes (powered by MyScheme portal data).</div>', unsafe_allow_html=True)

# Display chat history
display_chat_history()

# Create a container for the input and output
with st.container():
    # Create a form for the query input
    with st.form(key='query_form', clear_on_submit=True):
        query = st.text_input("Enter your question here", "")
        submit_button = st.form_submit_button(label='Submit')
        
    # Add a clear history button
    if st.button("Clear Chat History"):
        clear_history()
        st.experimental_rerun()

    if submit_button and query:
        with st.spinner("Getting answer..."):
            qa_chain = load_qa_chain()
            result = qa_chain.invoke({'query': query})

            # Extract only the answer
            final_answer = extract_answer(result["result"])

            # Add to chat history
            st.session_state.chat_history.append((query, final_answer))
            
            # Display the latest answer
            st.markdown('<div class="answer-section">', unsafe_allow_html=True)
            st.subheader("Answer:")
            st.markdown(final_answer)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Optional: Display source documents for debugging
            # with st.expander("Source Documents"):
            #     for i, doc in enumerate(result["source_documents"]):
            #         st.write(f"Document {i+1}:")
            #         st.write(doc.page_content)
            #         st.write("---")