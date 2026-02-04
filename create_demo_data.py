#!/usr/bin/env python3
"""
Demo data script for CornHub
Creates sample users, repositories, and issues for demonstration purposes.
"""

import requests
import json
import base64
import sys
from time import sleep

# Configuration
API_BASE = "http://localhost:8080"

# Sample data
DEMO_USERS = [
    {"username": "admin", "email": "admin@cornhub.local", "password": "admin123", "tier": "admin"},
    {"username": "alice", "email": "alice@cornhub.local", "password": "alice123", "tier": "developer"},
    {"username": "bob", "email": "bob@cornhub.local", "password": "bob123", "tier": "developer"},
    {"username": "charlie", "email": "charlie@cornhub.local", "password": "charlie123", "tier": "tester"}
]

DEMO_REPOS = [
    {"reponame": "awesome-web-app", "description": "A fantastic web application"},
    {"reponame": "machine-learning-toolkit", "description": "ML tools and utilities"},
    {"reponame": "mobile-game-engine", "description": "Cross-platform game engine"},
    {"reponame": "data-visualization", "description": "Beautiful charts and graphs"}
]

DEMO_ISSUES = [
    {
        "title": "Login button not working",
        "body": "When I click the login button, nothing happens. No error message or redirect.\n\nSteps to reproduce:\n1. Go to login page\n2. Enter valid credentials\n3. Click login button\n4. Nothing happens\n\nExpected: Should redirect to dashboard\nActual: Button appears to do nothing"
    },
    {
        "title": "Add dark mode support",
        "body": "It would be great to have a dark mode theme for better viewing in low light conditions.\n\nFeature requirements:\n- Toggle switch in settings\n- Persist user preference\n- Apply to all pages\n- Smooth transitions"
    },
    {
        "title": "Database migration failing",
        "body": "The latest database migration script is failing with a foreign key constraint error.\n\nError message:\npsycopg2.IntegrityError: insert or update on table \"users\" violates foreign key constraint\n\nNeed to investigate and fix the migration script."
    },
    {
        "title": "Performance optimization needed",
        "body": "Page load times are getting slow, especially on the repository list page.\n\nObservations:\n- Initial load takes 3-5 seconds\n- Pagination is slow\n- API responses are large\n\nSuggestions:\n- Implement lazy loading\n- Add caching\n- Optimize database queries"
    }
]

DEMO_COMMENTS = [
    "I can confirm this issue exists. Same problem on my machine.",
    "This is a high priority issue. We should fix it in the next release.",
    "I've been working on this. Will have a fix ready by tomorrow.",
    "Great idea! This would definitely improve user experience.",
    "I've created a branch to work on this feature. Will submit PR soon.",
    "Fixed in commit abc123. Please test and confirm.",
    "Tested the fix, works perfectly now. Thanks!",
    "This might be related to issue #2. Should we investigate together?",
    "I think we should also consider mobile responsiveness for this feature.",
    "Documentation updated to reflect these changes."
]

def get_auth_header(username, password):
    """Get HTTP Basic Auth header."""
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}

def create_users():
    """Create demo users."""
    print("🧑 Creating demo users...")
    created_users = []
    
    for i, user_data in enumerate(DEMO_USERS):
        try:
            response = requests.post(
                f"{API_BASE}/users",
                json={
                    "username": user_data["username"],
                    "email": user_data["email"], 
                    "password": user_data["password"]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                created_users.append(user_data)
                print(f"   ✅ Created user: {user_data['username']}")
            else:
                print(f"   ⚠️  User {user_data['username']} may already exist")
                created_users.append(user_data)  # Add anyway for auth
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Failed to create user {user_data['username']}: {e}")
            
        sleep(0.5)  # Rate limiting
    
    return created_users

def create_repositories(users):
    """Create demo repositories."""
    print("\n📁 Creating demo repositories...")
    created_repos = []
    
    for i, repo_data in enumerate(DEMO_REPOS):
        # Use different users as maintainers
        maintainer = users[i % len(users)]
        auth_header = get_auth_header(maintainer["username"], maintainer["password"])
        
        try:
            response = requests.post(
                f"{API_BASE}/repos",
                json={"reponame": repo_data["reponame"], "maintainer_id": 0},
                headers=auth_header,
                timeout=10
            )
            
            if response.status_code == 200:
                repo_info = response.json()
                created_repos.append({
                    **repo_info,
                    "maintainer": maintainer
                })
                print(f"   ✅ Created repository: {repo_data['reponame']}")
            else:
                print(f"   ❌ Failed to create repository {repo_data['reponame']}: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Failed to create repository {repo_data['reponame']}: {e}")
            
        sleep(0.5)
    
    return created_repos

def create_issues(repos, users):
    """Create demo issues."""
    print("\n🐛 Creating demo issues...")
    created_issues = []
    
    for repo in repos:
        repo_id = repo["repo_id"]
        repo_name = repo["reponame"]
        
        # Create 2-3 issues per repository
        num_issues = min(len(DEMO_ISSUES), 3)
        
        for i in range(num_issues):
            # Use different users as issue authors
            author = users[i % len(users)]
            auth_header = get_auth_header(author["username"], author["password"])
            
            issue_data = DEMO_ISSUES[i % len(DEMO_ISSUES)]
            
            try:
                response = requests.post(
                    f"{API_BASE}/repos/{repo_id}/issues",
                    json=issue_data,
                    headers=auth_header,
                    timeout=10
                )
                
                if response.status_code == 200:
                    issue_info = response.json()
                    created_issues.append({
                        **issue_info,
                        "repo_id": repo_id,
                        "author": author
                    })
                    print(f"   ✅ Created issue in {repo_name}: {issue_data['title']}")
                else:
                    print(f"   ❌ Failed to create issue in {repo_name}: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Failed to create issue in {repo_name}: {e}")
                
            sleep(0.5)
    
    return created_issues

def create_comments(issues, users):
    """Create demo comments."""
    print("\n💬 Creating demo comments...")
    
    for issue in issues:
        repo_id = issue["repo_id"]
        issue_num = issue["issue_num"]
        
        # Add 1-3 comments per issue
        num_comments = min(len(DEMO_COMMENTS), 3)
        
        for i in range(num_comments):
            # Use different users as commenters
            commenter = users[i % len(users)]
            auth_header = get_auth_header(commenter["username"], commenter["password"])
            
            comment_text = DEMO_COMMENTS[i % len(DEMO_COMMENTS)]
            
            try:
                response = requests.post(
                    f"{API_BASE}/repos/{repo_id}/issues/{issue_num}/comments",
                    json={"body": comment_text},
                    headers=auth_header,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Added comment to issue #{issue_num}")
                else:
                    print(f"   ❌ Failed to add comment to issue #{issue_num}: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Failed to add comment to issue #{issue_num}: {e}")
                
            sleep(0.5)

def check_server():
    """Check if the CornHub server is running."""
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def main():
    """Main function to create all demo data."""
    print("🌽 CornHub Demo Data Creator")
    print("=" * 40)
    
    # Check if server is running
    if not check_server():
        print(f"❌ Error: CornHub server is not running on {API_BASE}")
        print("Please start the server first:")
        print("   ./start.sh")
        print("   OR")
        print("   uvicorn app.main:app --reload --port 8080")
        sys.exit(1)
    
    print(f"✅ Server is running on {API_BASE}")
    
    try:
        # Create demo data
        users = create_users()
        if not users:
            print("❌ Failed to create any users. Exiting.")
            sys.exit(1)
            
        repos = create_repositories(users)
        if not repos:
            print("❌ Failed to create any repositories. Exiting.")
            sys.exit(1)
            
        issues = create_issues(repos, users)
        if issues:
            create_comments(issues, users)
        
        print("\n" + "=" * 40)
        print("🎉 Demo data created successfully!")
        print(f"\n📊 Summary:")
        print(f"   👥 Users: {len(users)}")
        print(f"   📁 Repositories: {len(repos)}")
        print(f"   🐛 Issues: {len(issues)}")
        
        print("\n🔑 Login credentials:")
        for user in users:
            print(f"   {user['username']} : {user['password']} ({user['tier']})")
            
        print(f"\n🌐 Access the frontend at: {API_BASE}/")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo data creation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()