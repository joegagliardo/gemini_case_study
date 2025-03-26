# def pdf_load(path: str):
#     #url = "https://abc.xyz/assets/investor/static/pdf/20230203_alphabet_10K.pdf"
#     loader = PyPDFLoader(path)
#     documents = loader.load()
#     return documents

# def pdf_page_to_base64_image(pdf_path_or_uri: str, page_num: int = 0) -> str:
#     """
#     Converts a specific page of a PDF to a base64 encoded PNG image.
#     Handles both local file paths and GCS URIs (gs://...).
#     If a GCS URI is provided, downloads the file to a temporary location first.
#     """
#     import re
#     import tempfile

#     temp_file_path = None
#     actual_pdf_path = pdf_path_or_uri
#     doc = None # Initialize doc to None

#     try:
#         # --- Step 1: Handle GCS path if necessary ---
#         if pdf_path_or_uri.startswith("gs://"):
#             print(f"Fetching from GCS path: {pdf_path_or_uri}")
#             # Parse GCS path
#             match = re.match(r"gs://([^/]+)/(.+)", pdf_path_or_uri)
#             if not match:
#                 raise ValueError(f"Invalid GCS path format: {pdf_path_or_uri}")
#             bucket_name, blob_name = match.groups()

#             # Create a temporary file
#             # delete=False is important so fitz.open can use the path,
#             # and we manually clean it up in the finally block.
#             # Using a suffix helps identify the file type if needed.
#             with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_f:
#                 temp_file_path = temp_f.name # Get the temporary file path

#             print(f"Created temporary file: {temp_file_path}")

#             # Download the GCS blob to the temporary file
#             try:
#                 storage_client = storage.Client()
#                 bucket = storage_client.bucket(bucket_name)
#                 blob = bucket.blob(blob_name)

#                 print(f"Downloading gs://{bucket_name}/{blob_name} to {temp_file_path}...")
#                 blob.download_to_filename(temp_file_path)
#                 print("Download complete.")
#                 actual_pdf_path = temp_file_path # Use the temp path for processing
#             except Exception as e:
#                 # Clean up temp file immediately if download fails
#                 if temp_file_path and os.path.exists(temp_file_path):
#                     os.remove(temp_file_path)
#                     print(f"Cleaned up temporary file {temp_file_path} after download error.")
#                 raise RuntimeError(f"Error downloading from GCS {pdf_path_or_uri}: {e}") from e
#         else:
#             # It's a local path, check if it exists
#             print(f"Using local path: {actual_pdf_path}")
#             if not os.path.exists(actual_pdf_path):
#                  raise FileNotFoundError(f"No such local file: {actual_pdf_path}")

#         # --- Step 2: Process the PDF (using actual_pdf_path) ---
#         print(f"Opening PDF: {actual_pdf_path}")
#         doc = fitz.open(actual_pdf_path) # Open local or temporary file

#         if page_num >= len(doc):
#             raise ValueError(f"Page number {page_num} out of range for PDF with {len(doc)} pages.")
#         page = doc.load_page(page_num)

#         # Increase resolution
#         zoom = 2
#         mat = fitz.Matrix(zoom, zoom)
#         pix = page.get_pixmap(matrix=mat)

#         # Convert to PNG bytes using Pillow
#         img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
#         img_byte_arr = io.BytesIO()
#         img.save(img_byte_arr, format='PNG')
#         img_byte_value = img_byte_arr.getvalue()

#         # Encode to base64
#         b64_encoded = base64.b64encode(img_byte_value).decode('utf-8')
#         print("PDF page processed successfully.")
#         return b64_encoded

#     except Exception as e:
#         print(f"Error processing PDF '{pdf_path_or_uri}' for page {page_num}: {e}")
#         # Re-raise the exception to signal failure
#         raise
#     finally:
#         # --- Step 3: Cleanup ---
#         # Close the fitz document if it was opened
#         if doc:
#             try:
#                 doc.close()
#                 print("Closed PDF document.")
#             except Exception as e:
#                  print(f"Warning: Error closing PDF document: {e}") # Non-critical usually

#         # Remove the temporary file if one was created
#         if temp_file_path and os.path.exists(temp_file_path):
#             try:
#                 os.remove(temp_file_path)
#                 print(f"Successfully cleaned up temporary file: {temp_file_path}")
#             except OSError as e:
#                 # Log error if cleanup fails, but don't crash
#                 print(f"Warning: Could not remove temporary file {temp_file_path}: {e}")
