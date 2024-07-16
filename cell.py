from google.colab import auth
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from requests import get
from socket import gethostname, gethostbyname
import subprocess
from google.colab import files
from urllib.parse import unquote
import io
import requests
import json

output_format = 'pdf'  # Change to 'html', 'markdown', 'latex', 'script', or 'slides' as needed
ip = gethostbyname(gethostname())
response = get(f"http://{ip}:9000/api/sessions").json()

file_id = response[0]['notebook']['path'].split('fileId=')[1]
notebook_name = unquote(response[0]['notebook']['name'])
notebook_path = f'/content/{notebook_name}.ipynb' if not notebook_name.endswith(".ipynb") else f'/content/{notebook_name}'
print(f"File ID: {file_id}")
print(f"Notebook Name: {notebook_name}")

def save_notebook_as_ipynb(file_id, path='notebook.ipynb', authenticated=False):
    if not authenticated:
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        response = requests.get(download_url)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            try:
                with open(path, 'r') as f:
                    json.load(f)
                print(f"Notebook saved as {path}")
                return True
            except json.JSONDecodeError:
                print("Downloaded file is not a valid JSON. Authentication may be required.")
                return False
        else:
            print("Failed to download the notebook.")
            return False
    else:
        auth.authenticate_user()
        creds, _ = default()
        drive_service = build('drive', 'v3', credentials=creds)
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.FileIO(path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")

        print(f"Notebook saved as {path}")
        return True

def convert_notebook(output_format):
    print(f"Converting notebook to {output_format}...")
    result = subprocess.run(
        ["jupyter", "nbconvert", f"--to", output_format, notebook_path],
        capture_output=True, text=True)

    if result.returncode == 0:
        print(f"Notebook converted to {output_format} successfully.")
        return notebook_path.replace('.ipynb', f'.{output_format}')
    else:
        print(f"Error converting notebook to {output_format}: {result.stderr}")
        return None

if not save_notebook_as_ipynb(file_id, notebook_path):
    print("Access denied or invalid file. Trying authenticated download...")
    if save_notebook_as_ipynb(file_id, notebook_path, authenticated=True):
        print("Downloading dependecies...")
        subprocess.run(['pip', 'install', '-q', 'nbconvert'])
        if output_format == 'pdf':
            subprocess.run(['apt-get', 'install', '-y', '-qq', 'texlive-xetex', 'texlive-fonts-recommended', 'texlive-plain-generic', 'pandoc'])

        converted_path = convert_notebook(output_format)

        if converted_path:
            print(f"Notebook saved as {converted_path}")
            files.download(converted_path)
        else:
            print(f"Failed to convert notebook to {output_format} after authentication.")
else:
    print("Downloading dependecies...")
    subprocess.run(['pip', 'install', '-q', 'nbconvert'])
    if output_format == 'pdf':
        subprocess.run(['apt-get', 'install', '-y', '-qq', 'texlive-xetex', 'texlive-fonts-recommended', 'texlive-plain-generic'])

    converted_path = convert_notebook(output_format)

    if converted_path:
        print(f"Notebook saved as {converted_path}")
        files.download(converted_path)
    else:
        print(f"Failed to convert notebook to {output_format}.")
