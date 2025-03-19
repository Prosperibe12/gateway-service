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

def get_next_artifact_number(container_client, branch_name):
    blobs = container_client.list_blobs()
    max_number = 0
    prefix = f"{branch_name}_#"
    for blob in blobs:
        if blob.name.startswith(prefix):
            try:
                # Extract the number from the blob name (e.g., "myrepo_#1/auth_repo.zip")
                number = int(blob.name.split('#')[1].split('/')[0])
                if number > max_number:
                    max_number = number
            except (IndexError, ValueError):
                continue
    return max_number + 1

def upload_to_azure(connection_string, repo_path, repo_name, branch_name):
    # Hardcoded container name
    container_name = "trendsartifact"

    # Zip the entire repository (excluding .git)
    output_zip_path = f"{branch_name}_repo.zip"
    zip_repo(repo_path, output_zip_path)

    # Connect to Azure Blob Storage
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    # Ensure the container exists
    if not container_client.exists():
        container_client.create_container()

    # Get the next artifact number for the repository
    artifact_number = get_next_artifact_number(container_client, branch_name)
    # blob_name = f"{repo_name}_#{artifact_number}/{branch_name}_repo.zip"
    blob_name = f"{branch_name}_#{artifact_number}/{branch_name}_{artifact_number}.zip"

    # Upload the zipped repository
    with open(output_zip_path, "rb") as data:
        container_client.upload_blob(name=blob_name, data=data)

    print(f"Uploaded {output_zip_path} as {blob_name}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python upload_to_azure.py <connection_string> <repo_path> <repo_name> <branch_name>")
        sys.exit(1)

    connection_string = sys.argv[1]
    repo_path = sys.argv[2]
    repo_name = sys.argv[3]
    branch_name = sys.argv[4]

    upload_to_azure(connection_string, repo_path, repo_name, branch_name)