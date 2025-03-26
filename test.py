import vertexai
import os

PROJECT_ID = "qwiklabs-gcp-01-c5bb17587754"  # @param {type:"string"}
REGION = "us-central1"  # @param {type:"string"}
os.environ['USER_AGENT'] = 'MyLangChainSignatureApp/1.0'

# Initialize Vertex AI SDK
vertexai.init(project=PROJECT_ID, location=REGION)
from langchain_google_vertexai import VertexAI
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
llm = VertexAI(model_name="gemini-2.0-flash-001", verbose=True)
embeddings = VertexAIEmbeddings("text-embedding-004")


my_text = "What day comes after Friday?"

resp = llm.invoke(my_text)
print(resp)


import check_pdf_signature as p
pdf = p.pdf_page_to_base64_image('gs://qwiklabs-gcp-01-c5bb17587754/Federal SW Template Signed.pdf', 1)
print(pdf)


print('Done')


# url = "https://abc.xyz/assets/investor/static/pdf/20230203_alphabet_10K.pdf"
# loader = PyPDFLoader(url)
# documents = loader.load()

