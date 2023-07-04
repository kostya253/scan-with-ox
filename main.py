import requests
import base64
from datetime import datetime

# GitHub API endpoint for fetching repositories
REPO_API = "https://api.github.com/user/repos"

# GitHub API endpoint for creating a file
CREATE_FILE_API = "https://api.github.com/repos/{}/{}/contents/{}"

# GitHub personal access token with repo scope
ACCESS_TOKEN = "Fill ME"

# OX Security yml file contents
FILE_CONTENT = """name: Example workflow with OX Security Scan
on:
  push:
    branches:
      - master
  pull_request:
    types: [opened, reopened, synchronize]
    branches:
      - master
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - name: Run OX Security Scan to check for vulnerabilities
        with:
          ox_api_key: ${{ secrets.OX_API_KEY }}
          ox_host_url: https://FILL ME
        uses: oxsecurity/ox-security-scan@main"""


def run_operation(prompt):
    answer = input(prompt)
    if answer == "y":
        return True
    else:
        return False


def fetch_username():
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    url = f"https://api.github.com/user"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting user information: {response.status_code}")
        return {}


def fetch_all_orgs():
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    url = f"https://api.github.com/user/orgs"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return []


def fetch_org_repos(user):
    repos = []
    page = 1
    per_page = 100
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    url = f"https://api.github.com/users/{user}/repos?page={page}&per_page={per_page}"
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            repos.extend(response.json())
            if len(response.json()) < per_page:
                break
            page += 1
            url = f"{REPO_API}?page={page}&per_page={per_page}"
        else:
            print(f"Error: {response.status_code}")
            break
    return repos


# Fetch all repositories using the GitHub API
def fetch_all_repos():
    repos = []
    page = 1
    per_page = 100
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    url = f"{REPO_API}?page={page}&per_page={per_page}"
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            repos.extend(response.json())
            if len(response.json()) < per_page:
                break
            page += 1
            url = f"{REPO_API}?page={page}&per_page={per_page}"
        else:
            print(f"Error: {response.status_code}")
            break
    return repos


# Create a new file with today's date in each repository
def create_file_in_repos(repos):
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    should_run_everytime = False

    for repo in repos:
        if not should_run_everytime:
            should_run_everytime = run_operation(
                f"Do you want to continue for rest of the repositories automatically, or check the changes for {repo['name']} first? (y - continue/n - check changes first): "
            )

        owner = repo["owner"]["login"]
        repo_name = repo["name"]

        # Skip public repos
        if not repo["private"] == True:
            continue

        file_name = f"build.yml"
        file_path = f".github/workflows/{file_name}"
        file_content = base64.b64encode(FILE_CONTENT.encode("utf-8")).decode("utf-8")
        payload = {
            "message": f"Add new file: {file_name}",
            "content": file_content,
            "branch": "master",
        }
        response = requests.put(
            CREATE_FILE_API.format(owner, repo_name, file_path),
            headers=headers,
            json=payload,
        )
        if response.status_code == 201:
            print(f"File created in {repo_name} repository")
        elif response.status_code == 422:
            print(
                f"ox-pipeline-scanner.yml is already created in {repo_name}, updating..."
            )

            payload = {
                "message": f"Update file: {file_name}",
                "content": file_content,
                "branch": "master",
                "sha": get_file_hash(owner, repo_name, file_path),
            }

            update_file(owner, repo_name, file_path, payload)
        else:
            print(f"Failed to create file in {repo_name} repository: {response.text}")


def get_file_hash(owner, repo_name, file_name):
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    url = "https://api.github.com/repos/{}/{}/contents/{}".format(
        owner, repo_name, file_name
    )
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_hash = response.json()["sha"]
        return file_hash
    else:
        return None


def update_file(owner, repo_name, file_name, new_content):
    url = "https://api.github.com/repos/{}/{}/contents/{}".format(
        owner, repo_name, file_name
    )
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}

    # create random number

    response = requests.put(url, headers=headers, json=new_content)
    if response.status_code == 200:
        print("File updated successfully.")
    else:
        print("Error updating file.")


# Main program
def main():
    print("OX Pipeline updater v1.0")

    # Fetch organizations
    orgs = fetch_all_orgs()

    if orgs:
        for org in orgs:
            org_repos = fetch_org_repos(org["login"])
            if org_repos:
                create_file_in_repos(org_repos)

    # Fetch user's repositories
    repos = fetch_all_repos()
    if repos:
        # Create a file in each repository
        create_file_in_repos(repos)


if __name__ == "__main__":
    main()
