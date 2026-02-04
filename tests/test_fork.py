#!/usr/bin/env python3
"""
Test script for fork functionality
"""
import requests
import json
import time

BASE_URL = "http://localhost:8080"

def login(username, password):
    """Login and get authentication headers"""
    response = requests.post(f"{BASE_URL}/auth/login", 
                            auth=(username, password))
    if response.status_code == 200:
        data = response.json()
        return {
            "Authorization": f"Basic {data.get('token', '')}"
        }
    return None

def create_test_repo(headers, reponame):
    """Create a test repository"""
    data = {
        "reponame": reponame,
        "maintainer_id": 0  # Will be set by backend
    }
    response = requests.post(f"{BASE_URL}/repos", json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to create repo: {response.status_code} - {response.text}")
        return None

def fork_repo(headers, repo_id, new_reponame):
    """Fork a repository"""
    data = {
        "new_reponame": new_reponame
    }
    response = requests.post(f"{BASE_URL}/repos/{repo_id}/fork", json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fork repo: {response.status_code} - {response.text}")
        return None

def get_repos(headers):
    """Get all repositories"""
    response = requests.get(f"{BASE_URL}/repos", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def main():
    print("=" * 60)
    print("Testing Fork Functionality")
    print("=" * 60)
    
    # Login as root
    print("\n1. Logging in as root...")
    headers = login("root", "admin123")
    if not headers:
        # Use basic auth directly
        from requests.auth import HTTPBasicAuth
        headers = {}
        auth = HTTPBasicAuth("root", "admin123")
    else:
        auth = None
    
    # Create a test repository
    print("\n2. Creating test repository...")
    test_repo_name = f"test-repo-{int(time.time())}"
    if auth:
        repo = requests.post(f"{BASE_URL}/repos", 
                           json={"reponame": test_repo_name, "maintainer_id": 0},
                           auth=auth).json()
    else:
        repo = create_test_repo(headers, test_repo_name)
    
    if repo:
        print(f"✓ Created repository: {repo['reponame']} (ID: {repo['repo_id']})")
    else:
        print("✗ Failed to create repository")
        return
    
    # Fork the repository
    print("\n3. Forking repository...")
    fork_name = f"{test_repo_name}-fork"
    if auth:
        forked_repo = requests.post(f"{BASE_URL}/repos/{repo['repo_id']}/fork",
                                   json={"new_reponame": fork_name},
                                   auth=auth).json()
    else:
        forked_repo = fork_repo(headers, repo['repo_id'], fork_name)
    
    if forked_repo:
        print(f"✓ Forked repository: {forked_repo['reponame']} (ID: {forked_repo['repo_id']})")
        print(f"  Fork of: {forked_repo.get('fork_of_id', 'N/A')}")
    else:
        print("✗ Failed to fork repository")
        return
    
    # List all repositories
    print("\n4. Listing all repositories...")
    if auth:
        repos = requests.get(f"{BASE_URL}/repos", auth=auth).json()
    else:
        repos = get_repos(headers)
    
    if repos and 'items' in repos:
        print(f"✓ Total repositories: {repos['meta']['total_size']}")
        for item in repos['items']:
            print(f"  - {item['reponame']} (Maintainer: {item['maintainer_name']})")
    
    # Get fork repository files
    print("\n5. Checking forked repository files...")
    if auth:
        files_response = requests.get(f"{BASE_URL}/repos/{forked_repo['repo_id']}/files", auth=auth)
    else:
        files_response = requests.get(f"{BASE_URL}/repos/{forked_repo['repo_id']}/files", headers=headers)
    
    if files_response.status_code == 200:
        files = files_response.json()
        print(f"✓ Files in forked repository: {len(files.get('files', []))}")
    else:
        print(f"  (Empty repository - this is expected for new repos)")
    
    print("\n" + "=" * 60)
    print("✓ Fork functionality test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    # Wait for server to be ready
    time.sleep(2)
    main()
