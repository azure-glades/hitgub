import urllib.request
import urllib.error
import urllib.parse
import json
import base64
import time
import os
import subprocess
import sys

BASE_URL = "http://localhost:8080"

def get_auth_header(username, password):
    user_pass = f"{username}:{password}"
    b64_val = base64.b64encode(user_pass.encode()).decode()
    return {"Authorization": f"Basic {b64_val}"}

def make_request(method, endpoint, data=None, auth=None, expect_status=200):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if auth:
        headers.update(auth)
    
    if data:
        json_data = json.dumps(data).encode('utf-8')
    else:
        json_data = None
    
    req = urllib.request.Request(url, data=json_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode()
            print(f"[{method}] {endpoint} -> Status: {status}")
            if status != expect_status:
                print(f"FAIL: Expected {expect_status}, got {status}")
                print(f"Body: {body}")
                return None
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode()
        print(f"[{method}] {endpoint} -> Status: {status} (Expected: {expect_status})")
        if status != expect_status:
            print(f"FAIL: Expected {expect_status}, got {status}")
            print(f"Body: {body}")
            return None
        return json.loads(body) if body else {}
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def main():
    print("WARNING: Make sure the server is running on localhost:8000")
    
    # 1. Create Users (Open endpoint)
    print("\n--- Creating Users ---")
    user1 = f"user_{int(time.time())}"
    user2 = f"user2_{int(time.time())}"
    pass1 = "secret1"
    pass2 = "secret2"
    
    u1_res = make_request("POST", "/users", {"username": user1, "email": f"{user1}@example.com", "password": pass1}, expect_status=200)
    u2_res = make_request("POST", "/users", {"username": user2, "email": f"{user2}@example.com", "password": pass2}, expect_status=200)
    
    if not u1_res or not u2_res:
        print("Failed to create users. Exiting.")
        return

    uid1 = u1_res['user_id']
    uid2 = u2_res['user_id']
    print(f"Created {user1} (id={uid1}) and {user2} (id={uid2})")

    # 2. Create Role
    print("\n--- Creating Role ---")
    # Roles endpoint is not protected in my implementation, or is it?
    # Checked main.py: @app.post("/roles") -> NOT DEPENDS(auth). Open.
    role_name = "developer"
    # Check if role exists first (list roles)
    roles = make_request("GET", "/roles")
    role_id = None
    for r in roles:
        if r['rolename'] == role_name:
            role_id = r['role_id']
            break
    
    if not role_id:
        r_res = make_request("POST", "/roles", {"rolename": role_name}, expect_status=201)
        if r_res:
            role_id = r_res['role_id']
    
    print(f"Role '{role_name}' has id {role_id}")

    # 3. Create Repo (Authenticated as User 1)
    print("\n--- Creating Repo (User 1) ---")
    repo_name = f"repo_{int(time.time())}"
    repo_res = make_request("POST", "/repos", 
                            {"reponame": repo_name, "maintainer_id": 0}, # maintainer_id is ignored/overridden
                            auth=get_auth_header(user1, pass1),
                            expect_status=200)
    
    if not repo_res:
        print("Failed to create repo")
        return
    
    repo_id = repo_res['repo_id']
    print(f"Created repo '{repo_name}' (id={repo_id}) with owner {user1}")

    # 4. Verify User 2 cannot access Repo issues (No access granted yet)
    print("\n--- Checking Access Denied (User 2) ---")
    # Try to Read Issues
    make_request("GET", f"/repos/{repo_id}/issues", 
                 auth=get_auth_header(user2, pass2), 
                 expect_status=403)

    # 5. Grant Access (User 1 grants User 2)
    print("\n--- Granting Access (User 1 -> User 2) ---")
    make_request("POST", "/access", 
                 {"user_id": uid2, "repo_id": repo_id, "role_id": role_id},
                 auth=get_auth_header(user1, pass1),
                 expect_status=201)

    # 6. Verify User 2 CAN access now
    print("\n--- Checking Access Granted (User 2) ---")
    # Create Issue
    make_request("POST", f"/repos/{repo_id}/issues", 
                 {"title": "Bug fix", "body": "fix it"},
                 auth=get_auth_header(user2, pass2), 
                 expect_status=200)
    
    # 7. Verify Unauthenticated Git Access Denied
    print("\n--- Checking Git Info Refs (No Auth) ---")
    # Using curl-like request for git endpoint
    # git endpoints are basically GET/POST.
    try:
        url = f"{BASE_URL}/{repo_name}.git/info/refs?service=git-upload-pack"
        req = urllib.request.Request(url)
        urllib.request.urlopen(req)
        print("FAIL: Git info/refs accessible without auth")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("PASS: Git info/refs required auth (401)")
        else:
            print(f"FAIL: Git info/refs returned {e.code}")

    print("\nTests Completed.")

if __name__ == "__main__":
    main()
