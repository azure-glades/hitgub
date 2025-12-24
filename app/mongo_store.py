from datetime import datetime, timezone
from pymongo import MongoClient
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017")
db = client["issue_threads"]

def create_issue_doc(issue_id: int, title: str, author: str) -> str:
    doc = {
        "issue_id": issue_id,
        "title": title,
        "author": author,
        "created_at": datetime.now(timezone.utc),
        "comments": []
    }
    ins_id = db.threads.insert_one(doc).inserted_id
    return ins_id

def add_comment(thread_id: str, user: str, body: str) -> None:
    new_comment = {
        "user": user,
        "body": body,
        "timestamp": datetime.now(timezone.utc)
    }
    result = db.threads.update_one(
        {"_id": ObjectId(thread_id)},
        {"$push": {"comments": new_comment} }
    )

def get_issue(issue_id: str):
    doc = db.threads.find_one({"_id": ObjectId(issue_id)})
    if not doc:
        raise ValueError("Thread not found")
    doc["id"] = str(doc.pop("_id"))
    return doc