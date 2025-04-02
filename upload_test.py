def upload(filename = 'Federal SW Signed.pdf'):
    import requests
    """
    Uploads a PDF file to the server.
    """
    url = 'http://127.0.0.1:5001/upload'
    with open('Federal SW Signed.pdf', 'rb') as f:
        files = {'pdf_file': f}
        response = requests.post(url, files=files)
        print(response.text)

# upload()

import requests
pdf_unsigned = 'https://storage.googleapis.com/qwiklabs-gcp-01-c5bb17587754/Federal SW Template.pdf'
pdf_predict = 'https://storage.googleapis.com/qwiklabs-gcp-01-c5bb17587754/Federal SW Signed.pdf'

def test_webservice(file_name):
    url = "http://127.0.0.1:5001/is_signed"
    data = {"file_name": file_name}

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        print(f"Status Code: {response.status_code}")
        print(f"Response JSON: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


test_webservice(pdf_unsigned)
test_webservice(pdf_predict)