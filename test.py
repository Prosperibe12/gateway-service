import os
from azure.storage.blob import BlobServiceClient, ContainerClient
import zipfile
import sys

def zip_repo(repo_path, output_zip_path):
    with zipfile.ZipFile(output_zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(repo_path):
            # Exclude the .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, repo_path)
                zipf.write(file_path, arcname)

def get_next_folder_number(container_client, branch_name):
    blobs = container_client.list_blobs(name_starts_with=f"{branch_name}/")
    max_number = 0
    for blob in blobs:
        folder_name = blob.name.split('/')[1]  # Extract folder name (e.g., "auth/#1")
        if folder_name.startswith(branch_name):
            try:
                number = int(folder_name.split('#')[1])
                if number > max_number:
                    max_number = number
            except (IndexError, ValueError):
                continue
    return max_number + 1

def upload_to_azure(connection_string, container_name, repo_path, branch_name):

    # Zip the entire repository (excluding .git)
    output_zip_path = f"{branch_name}_repo.zip"
    zip_repo(repo_path, output_zip_path)

    # Connect to Azure Blob Storage
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    # Ensure the container exists
    if not container_client.exists():
        container_client.create_container()

    # Get the next folder number for the branch
    folder_number = get_next_folder_number(container_client, branch_name)
    folder_name = f"{branch_name}/#{folder_number}"

    # Upload the zipped repository
    blob_name = f"{folder_name}/{output_zip_path}"
    with open(output_zip_path, "rb") as data:
        container_client.upload_blob(name=blob_name, data=data)

    print(f"Uploaded {output_zip_path} to {blob_name}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python test.py <connection_string> <container_name> <repo_path> <branch_name>")
        sys.exit(1)

    connection_string = sys.argv[1]
    container_name = sys.argv[2]
    repo_path = sys.argv[3]
    branch_name = sys.argv[4]

    upload_to_azure(connection_string, container_name, repo_path, branch_name)