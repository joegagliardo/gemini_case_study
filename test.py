import vertexai
import os

# PROJECT_ID = "qwiklabs-gcp-01-c5bb17587754"  # @param {type:"string"}
PROJECT_ID = "roi-genai-joey"  # @param {type:"string"}
REGION = "us-central1"  # @param {type:"string"}
os.environ['USER_AGENT'] = 'MyLangChainSignatureApp/1.0'

# Initialize Vertex AI SDK
vertexai.init(project=PROJECT_ID, location=REGION)
from langchain_google_vertexai import VertexAI
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
llm = VertexAI(model_name="gemini-2.0-flash-001", verbose=True)
embeddings = VertexAIEmbeddings("text-embedding-004")


# my_text = "What day comes after Friday?"

# resp = llm.invoke(my_text)
# print(resp)


import check_pdf_signature as p
pdf_unsigned = 'https://storage.googleapis.com/qwiklabs-gcp-01-c5bb17587754/Federal SW Template.pdf'
pdf_predict = 'https://storage.googleapis.com/qwiklabs-gcp-01-c5bb17587754/Federal SW Signed.pdf'
# pdf_predict = pdf_unsigned


print('Called as a simple prompt -> yes')
prompt = p.create_signed_pdf_prompt(pdf_unsigned, pdf_predict)
resp = llm.invoke(prompt)
print(resp)

print('Called as a simple prompt -> no')
prompt = p.create_signed_pdf_prompt(pdf_unsigned, pdf_unsigned)
resp = llm.invoke(prompt)
print(resp)

# print('Called as a human message')
# human_message = p.create_signed_pdf_human_message(pdf_unsigned, pdf_predict)
# resp = llm.invoke(human_message)
# print(resp)

print('Called as a chain -> yes')
signed_check_chain = p.create_signed_pdf_chain_vertex(llm, pdf_unsigned)
response = signed_check_chain.invoke(pdf_predict)
print(response)

print('Called as a chain -> no')
signed_check_chain = p.create_signed_pdf_chain_vertex(llm, pdf_unsigned)
response = signed_check_chain.invoke(pdf_unsigned)
print(response)

print('Done')


