import os
import io
from google.cloud import storage

import pypdf
from langchain_core.messages import HumanMessage, SystemMessage
# from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
# from langchain_core.documents import Document

def create_signed_pdf_prompt(document1: str, document2: str):
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

