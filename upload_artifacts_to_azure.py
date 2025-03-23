import os, zipfile, sys, re
from azure.storage.blob import BlobServiceClient

def extract_repository_name(repository_path):
    """Extract the repository name from the full repository path."""
    # Split the path by '/' and take the last part
    return repository_path.split('/')[-1]

def sanitize_container_name(repository_name):
    """Sanitize the repository name to make it a valid Azure container name."""
    # Replace invalid characters with '-'
    sanitized_name = re.sub(r'[^a-z0-9-]', '-', repository_name.lower())
    # Ensure the name is between 3 and 63 characters
    sanitized_name = sanitized_name[:63]
    return sanitized_name

def zip_repo(repo_path, output_zip_path):
    """Zip the repository, excluding the .git directory."""
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
    """Get the next folder number for the given branch."""
    blobs = container_client.list_blobs(name_starts_with=f"{branch_name}/")
    max_number = 0

    for blob in blobs:
        # Extract folder name (e.g., "branch/#1/artifact.zip")
        folder_name = blob.name.split('/')[1]  # Second part of the path
        if folder_name.startswith('#'):
            try:
                # Extract the number after the '#'
                number = int(folder_name[1:])
                if number > max_number:
                    max_number = number
            except (IndexError, ValueError):
                continue

    return max_number + 1

def upload_to_azure(connection_string, repo_path, repository_path, branch_name):
    """Zip the repository and upload it to Azure Blob Storage."""
    # Extract the repository name from the full path
    repository_name = extract_repository_name(repository_path)
    # Sanitize the repository name to create a valid container name
    container_name = sanitize_container_name(repository_name)

    # Zip the repository (excluding .git)
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

    print(f"Uploaded {output_zip_path} to {blob_name} in container {container_name}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python upload_artifacts_to_azure.py <connection_string> <repo_path> <repository_path> <branch_name>")
        sys.exit(1)

    connection_string = sys.argv[1]
    repo_path = sys.argv[2]
    repository_path = sys.argv[3]
    branch_name = sys.argv[4]

    upload_to_azure(connection_string, repo_path, repository_path, branch_name)