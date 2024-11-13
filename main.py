import requests
import base64
import argparse
from datetime import datetime

# GitHub API base URL
GITHUB_API_BASE = "api.github.com"  # Default value

# GitHub API endpoints - will be configured based on base URL
REPO_API = None
CREATE_FILE_API = None

# GitHub access token
ACCESS_TOKEN = "Fill ME"

# OX Security yml file contents
FILE_CONTENT = """name: Example workflow with OX Security Scan
on:
  push:
    branches:
      - main
  pull_request:
    types: [opened, reopened, synchronize]
    branches:
      - main
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - name: Run OX Security Scan to check for vulnerabilities
        with:
          ox_api_key: ${{ secrets.OX_API_KEY }}
          ox_host_url: https://Fill ME
        uses: oxsecurity/ox-security-scan@main"""


def configure_github_api(base_url=None):
    """Configure the GitHub API base URL and update endpoints accordingly."""
    global GITHUB_API_BASE, REPO_API, CREATE_FILE_API
    
    if base_url:
        GITHUB_API_BASE = base_url.rstrip('/')  # Remove trailing slash if present
    
    # Update the API endpoints with the configured base URL
    REPO_API = f"https://{GITHUB_API_BASE}/user/repos"
    CREATE_FILE_API = f"https://{GITHUB_API_BASE}/repos/{{0}}/{{1}}/contents/{{2}}"

    # review above
    print("github_api_base:", GITHUB_API_BASE)
    print("repo_api:", REPO_API)
    print("create_file_api:", CREATE_FILE_API)


def run_operation(prompt):
    answer = input(prompt)
    if answer == "y":
        return True
    else:
        return False


def fetch_username():
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    url = f"https://{GITHUB_API_BASE}/user"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting user information: {response.status_code}")
        return {}


def fetch_all_orgs():
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    url = f"https://{GITHUB_API_BASE}/user/orgs"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return []


def fetch_user_repos():
    repos = []
    page = 1
    per_page = 100
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    while True:
        url = f"https://{GITHUB_API_BASE}/user/repos?page={page}&per_page={per_page}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            current_batch = response.json()
            repos.extend(current_batch)
            if len(current_batch) < per_page:
                break
            page += 1
        else:
            print(f"Error: {response.status_code}")
            break
    return repos


def fetch_org_repos(org):
    repos = []
    page = 1
    per_page = 100
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    while True:
        url = f"https://{GITHUB_API_BASE}/orgs/{org}/repos?page={page}&per_page={per_page}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            current_batch = response.json()
            repos.extend(current_batch)
            if len(current_batch) < per_page:
                break  # Exit loop if we've fetched all repositories
            page += 1
        else:
            print(f"Error fetching repositories for organization {org}: {response.status_code}")
            break
    return repos


def create_file_in_repos(repos):
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    should_run_everytime = False

    # review repos
    print("private repositories:", [repo['name'] for repo in repos if repo['private'] == True])

    for repo in repos:
        if not should_run_everytime:
            should_run_everytime = run_operation(
                f"Do you want to continue for rest of the repositories automatically, or check the changes for {repo['name']} first? (y - continue/n - check changes first): "
            )

        owner = repo["owner"]["login"]
        repo_name = repo["name"]

        # Skip public repos
        if repo["private"] == False:
            continue

        file_name = f"ox-scan.yml"
        file_path = f".github/workflows/{file_name}"
        file_content = base64.b64encode(FILE_CONTENT.encode("utf-8")).decode("utf-8")
        payload = {
            "message": f"Add new file: {file_name}",
            "content": file_content,
            "branch": "main",
        }
        
        url = CREATE_FILE_API.format(owner, repo_name, file_path)
        response = requests.put(
            url,
            headers=headers,
            json=payload,
        )
        
        if response.status_code == 201:
            print(f"File {file_name} created in {repo_name} repository")
        elif response.status_code == 422:
            print(
                f"{file_name} is already present in the {repo_name} repo, updating..."
            )

            payload = {
                "message": f"Update file: {file_name}",
                "content": file_content,
                "branch": "main",
                "sha": get_file_hash(owner, repo_name, file_path),
            }

            update_file(owner, repo_name, file_path, payload)
        else:
            print(f"Failed to create file {file_name} in {repo_name} repository: {response.text}")


def get_file_hash(owner, repo_name, file_name):
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    url = f"https://{GITHUB_API_BASE}/repos/{owner}/{repo_name}/contents/{file_name}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_hash = response.json()["sha"]
        return file_hash
    else:
        return None


def update_file(owner, repo_name, file_name, new_content):
    url = f"https://{GITHUB_API_BASE}/repos/{owner}/{repo_name}/contents/{file_name}"
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}

    response = requests.put(url, headers=headers, json=new_content)
    if response.status_code == 200:
        print(f"File {file_name} updated successfully.")
    else:
        print(f"Error updating file {file_name}.")


def main(github_api_base=None):
    print("OX Pipeline updater v1.0")
    
    # Configure GitHub API with custom base URL if provided
    configure_github_api(github_api_base)
    
    # Fetch organizations
    orgs = fetch_all_orgs()
    
    if orgs:
        for org in orgs:
            org_repos = fetch_org_repos(org["login"])
            if org_repos:
                print("Processing org repos...")
                create_file_in_repos(org_repos)

    # Fetch user's repositories
    repos = fetch_user_repos()
    if repos:
        # Create a file in each repository
        print("Processing user repos...")
        create_file_in_repos(repos)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OX Pipeline updater')
    parser.add_argument('--github-api', 
                      help='GitHub API base URL (default: api.github.com)',
                      default=None)
    
    args = parser.parse_args()
    main(args.github_api)
