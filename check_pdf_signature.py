import os
import io
from google.cloud import storage

import pypdf
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
# from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
# from langchain_core.documents import Document

def create_signed_pdf_prompt(document1: str):
    """Creates the message to compare an unsigned base document to a second document to see if the second is signed."""
    if not document1:
        raise ValueError("You must supply a URI for the document.")

    ret = [
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "Analyze the attached image. It is the first page of a document. "
                        "Is there a handwritten signature or a digital signature block present "
                        "in the lower-right quadrant of the page of the document? "
                        "Answer only with 'Yes', 'No', or 'Uncertain'."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {"url": document1}
                }
            ]
        )
    ]
    return ret

def create_signed_pdf_prompt_with_example(document1: str, document2: str):
    """Creates the message to compare an unsigned base document to a second document to see if the second is signed."""
    if not document1 or not document2:
        raise ValueError("You must supply two URIs for the documents.")

    ret = [
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "Analyze the attached images. They are each the first page of a document. "
                        "The first document is not signed, in the lower right part of the page. "
                        "Is there a handwritten signature or a digital signature block present "
                        "in the lower-right quadrant of the page of the second document? "
                        "Answer only with 'Yes', 'No', or 'Uncertain'."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {"url": document1}
                },
                {
                    "type": "image_url",
                    "image_url": {"url": document2}
                },
            ]
        )
    ]
    return ret

# def create_signed_pdf_human_message(document1_uri: str, document2_uri: str) -> HumanMessage:
#     """
#     Creates a HumanMessage for comparing an unsigned base document to a second document
#     to see if the second is signed, using URIs.

#     Args:
#         document1_uri: The URI of the unsigned document image.
#         document2_uri: The URI of the potentially signed document image.

#     Returns:
#         A HumanMessage object ready to be used in a Langchain chain.
#     """

#     template = (
#         "Analyze the attached images. They are each the first page of a document. "
#         "The first document (URI: {document1_uri}) is not signed, in the lower right part of the page. "
#         "Is there a handwritten signature or a digital signature block present "
#         "in the lower-right quadrant of the page of the second document (URI: {document2_uri})? "
#         "Answer only with 'Yes', 'No', or 'Uncertain'."
#     )

#     formatted_prompt_text = template.format(
#         document1_uri=document1_uri,
#         document2_uri=document2_uri
#     )

#     final_message_content = [
#         {"type": "text", "text": formatted_prompt_text},
#         {"type": "image_url", "image_url": {"url": document1_uri}},
#         {"type": "image_url", "image_url": {"url": document2_uri}},
#     ]

#     return HumanMessage(content=final_message_content)



from langchain_core.runnables import RunnablePassthrough
from langchain_google_vertexai import ChatVertexAI
from typing import Dict, List
# from langchain.tools import tool

# @tool("check_document_signature_vertex", return_direct=False)
def create_signed_pdf_chain_vertex(llm: ChatVertexAI, unsigned_pdf_uri: str):
    """
    Creates a Langchain chain for comparing an unsigned base document to a second document
    to see if the second is signed, using URIs and Vertex AI.

    Args:
        llm: An instance of a Langchain ChatVertexAI model (configured for vision).
        unsigned_pdf_uri: The URI of the unsigned document.

    Returns:
        A Langchain Runnable chain that takes a single string (the URI of the second document)
        and returns the LLM's response.
    """

    # template = (
    #     "Analyze the attached images. They are each the first page of a document. "
    #     f"The first document (URI: {unsigned_pdf_uri}) is not signed, in the lower right part of the page. "
    #     "Is there a handwritten signature or a digital signature block present "
    #     "in the lower-right quadrant of the page of the second document (URI: {{pdf_uri}})? "
    #     "Answer only with 'Yes', 'No', or 'Uncertain'."
    # )
    template = (
        "Analyze the attached images. They are each the first page of a document. "
        f"The first document is not signed, in the lower right part of the page. "
        "Is there a handwritten signature or a digital signature block present "
        "in the lower-right quadrant of the page of the second document? "
        "Answer only with 'Yes', 'No', or 'Uncertain'."
    )

    prompt_template = PromptTemplate(template=template, input_variables=["unsigned_pdf_uri", "pdf_uri"])

    def format_messages(pdf_uri: str) -> List[HumanMessage]:
        return [
            HumanMessage(content=[
                {"type": "text", "text": prompt_template.format(pdf_uri=pdf_uri)},
                {"type": "image_url", "image_url": {"url": unsigned_pdf_uri}},
                {"type": "image_url", "image_url": {"url": pdf_uri}},
            ])
        ]

    return format_messages | llm
