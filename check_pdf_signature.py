import fitz  # PyMuPDF
import base64
import os
from PIL import Image
import io
from google.cloud import storage

# from dotenv import load_dotenv

# Import specifically for Google Gemini
# from langchain_google_genai import VertexAI

# from langchain_core.messages import HumanMessage
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.runnables import RunnableLambda, RunnablePassthrough

# # Load environment variables (for API keys)
# load_dotenv()

# --- Configuration ---
# Ensure GOOGLE_API_KEY is set in your environment or .env file
# Example: os.environ["GOOGLE_API_KEY"] = "YOUR_KEY"

# Configure the Gemini Pro Vision model
# Make sure you have access and the API key is correctly set
# try:
#     model = ChatGoogleGenerativeAI(model="gemini-pro-vision", temperature=0)
# except Exception as e:
#     print(f"Error initializing Gemini model: {e}")
#     print("Please ensure 'langchain-google-genai' is installed and GOOGLE_API_KEY is set.")
#     exit() # Exit if model can't be initialized
# # --- End Configuration ---


# def pdf_page_to_base64_image(pdf_path: str, page_num: int = 0) -> str:
#     """Converts a specific page of a PDF to a base64 encoded PNG image."""
#     try:
#         doc = fitz.open(pdf_path)
#         if page_num >= len(doc):
#             raise ValueError(f"Page number {page_num} out of range for PDF with {len(doc)} pages.")
#         page = doc.load_page(page_num)

#         # Increase resolution for potentially better analysis by the LLM
#         zoom = 2  # zoom factor
#         mat = fitz.Matrix(zoom, zoom)
#         pix = page.get_pixmap(matrix=mat)

#         # Use Pillow to convert to PNG bytes
#         img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
#         img_byte_arr = io.BytesIO()
#         img.save(img_byte_arr, format='PNG')
#         img_byte_arr = img_byte_arr.getvalue()

#         doc.close()
#         return base64.b64encode(img_byte_arr).decode('utf-8')
#     except Exception as e:
#         print(f"Error processing PDF {pdf_path}: {e}")
#         raise # Re-raise the exception after logging

def pdf_page_to_base64_image(pdf_path_or_uri: str, page_num: int = 0) -> str:
    """
    Converts a specific page of a PDF to a base64 encoded PNG image.
    Handles both local file paths and GCS URIs (gs://...).
    If a GCS URI is provided, downloads the file to a temporary location first.
    """
    import re
    import tempfile

    temp_file_path = None
    actual_pdf_path = pdf_path_or_uri
    doc = None # Initialize doc to None

    try:
        # --- Step 1: Handle GCS path if necessary ---
        if pdf_path_or_uri.startswith("gs://"):
            print(f"Fetching from GCS path: {pdf_path_or_uri}")
            # Parse GCS path
            match = re.match(r"gs://([^/]+)/(.+)", pdf_path_or_uri)
            if not match:
                raise ValueError(f"Invalid GCS path format: {pdf_path_or_uri}")
            bucket_name, blob_name = match.groups()

            # Create a temporary file
            # delete=False is important so fitz.open can use the path,
            # and we manually clean it up in the finally block.
            # Using a suffix helps identify the file type if needed.
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_f:
                temp_file_path = temp_f.name # Get the temporary file path

            print(f"Created temporary file: {temp_file_path}")

            # Download the GCS blob to the temporary file
            try:
                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)

                print(f"Downloading gs://{bucket_name}/{blob_name} to {temp_file_path}...")
                blob.download_to_filename(temp_file_path)
                print("Download complete.")
                actual_pdf_path = temp_file_path # Use the temp path for processing
            except Exception as e:
                # Clean up temp file immediately if download fails
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    print(f"Cleaned up temporary file {temp_file_path} after download error.")
                raise RuntimeError(f"Error downloading from GCS {pdf_path_or_uri}: {e}") from e
        else:
            # It's a local path, check if it exists
            print(f"Using local path: {actual_pdf_path}")
            if not os.path.exists(actual_pdf_path):
                 raise FileNotFoundError(f"No such local file: {actual_pdf_path}")

        # --- Step 2: Process the PDF (using actual_pdf_path) ---
        print(f"Opening PDF: {actual_pdf_path}")
        doc = fitz.open(actual_pdf_path) # Open local or temporary file

        if page_num >= len(doc):
            raise ValueError(f"Page number {page_num} out of range for PDF with {len(doc)} pages.")
        page = doc.load_page(page_num)

        # Increase resolution
        zoom = 2
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PNG bytes using Pillow
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_value = img_byte_arr.getvalue()

        # Encode to base64
        b64_encoded = base64.b64encode(img_byte_value).decode('utf-8')
        print("PDF page processed successfully.")
        return b64_encoded

    except Exception as e:
        print(f"Error processing PDF '{pdf_path_or_uri}' for page {page_num}: {e}")
        # Re-raise the exception to signal failure
        raise
    finally:
        # --- Step 3: Cleanup ---
        # Close the fitz document if it was opened
        if doc:
            try:
                doc.close()
                print("Closed PDF document.")
            except Exception as e:
                 print(f"Warning: Error closing PDF document: {e}") # Non-critical usually

        # Remove the temporary file if one was created
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"Successfully cleaned up temporary file: {temp_file_path}")
            except OSError as e:
                # Log error if cleanup fails, but don't crash
                print(f"Warning: Could not remove temporary file {temp_file_path}: {e}")

def create_vision_prompt(image_data: str) -> list:
    """Creates the message structure for the vision model."""
    # This structure works for Gemini Vision
    return [
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "Analyze the attached image, which is the first page of a document. "
                        "Is there a handwritten signature or a digital signature block present "
                        "in the lower-right quadrant of the page? "
                        "Answer only with 'Yes', 'No', or 'Uncertain'."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_data}"}
                },
            ]
        )
    ]

# # Define the LangChain Runnable sequence (using RunnableLambda for custom functions)
# check_signature_chain = (
#     RunnablePassthrough.assign( # Keep pdf_path input, add image_data
#         image_data=RunnableLambda(lambda x: pdf_page_to_base64_image(x["pdf_path"], page_num=0))
#     )
#     | RunnableLambda(lambda x: create_vision_prompt(x["image_data"])) # Create prompt messages
#     | model                                                          # Call the Gemini model
#     | StrOutputParser()                                              # Get the string response
#     | RunnableLambda(lambda text: text.strip().lower())             # Clean up response
# )

# # --- Function to Use ---
# def check_first_page_signature_lc(pdf_path: str) -> str:
#     """
#     Uses LangChain and Google Gemini to check for a signature
#     in the lower-right corner of the first page of a PDF.

#     Args:
#         pdf_path: The file path to the PDF document.

#     Returns:
#         A string indicating presence ('yes', 'no', 'uncertain')
#         or an error message.
#     """
#     if not os.path.exists(pdf_path):
#         return f"Error: PDF file not found at {pdf_path}"

#     try:
#         print(f"Processing {pdf_path} using Google Gemini...")
#         # Invoke the chain with the PDF path as input
#         result = check_signature_chain.invoke({"pdf_path": pdf_path})
#         print(f"LLM Raw Response: '{result}'") # Log raw response for debugging

#         # Basic interpretation (can be made more robust)
#         if "yes" in result:
#             return "yes"
#         elif "no" in result:
#             return "no"
#         else:
#             # Handle cases where the LLM didn't follow instructions exactly
#             print(f"Warning: LLM response '{result}' was not a clear yes/no. Interpreting as uncertain.")
#             return "uncertain"
#     except Exception as e:
#         return f"An error occurred: {e}"

# # --- Example Usage ---
# if __name__ == "__main__":
#     # Create a dummy PDF for testing if you don't have one
#     # (Requires reportlab: pip install reportlab)
#     try:
#         from reportlab.pdfgen import canvas
#         from reportlab.lib.pagesizes import letter
#         dummy_pdf_path = "dummy_signature_test.pdf"
#         c = canvas.Canvas(dummy_pdf_path, pagesize=letter)
#         width, height = letter
#         # Add some text
#         c.drawString(100, height - 100, "Sample Document - First Page")
#         c.drawString(100, height - 120, "Content goes here...")
#         # Add a fake "signature" line in the lower right
#         c.drawString(width - 200, 100, "_________________________")
#         c.drawString(width - 200, 85, "Signature")
#         c.save()
#         print(f"Created dummy PDF: {dummy_pdf_path}")
#         pdf_to_check = dummy_pdf_path
#     except ImportError:
#         print("reportlab not installed. Cannot create dummy PDF.")
#         print("Please provide a path to a real PDF file for testing.")
#         # Replace with the actual path to your PDF:
#         # pdf_to_check = "path/to/your/document.pdf" # <<< CHANGE THIS IF NEEDED
#         pdf_to_check = None # Ensure it's defined

#     if pdf_to_check and os.path.exists(pdf_to_check):
#         signature_status = check_first_page_signature_lc(pdf_to_check)
#         print(f"\nSignature detected in lower-right of first page: {signature_status}")
#     elif pdf_to_check:
#          print(f"Test PDF '{pdf_to_check}' not found. Please update the path.")
#     else:
#         print("No PDF path provided for checking.")
