from models import User, Repository

def create_user(db,user):
    actual_user=User(username=user.username, email=user.email, password_hash=user.password)
    db.add(actual_user)
    db.commit()
    db.refresh(actual_user)
    return actual_user

def get_user(db,user_id)
    temp=db.query(User).filter(User.user_id==user_id).first()
    return temp

def create_repo(db,repo):
    actual_repo=Repository(reponame=repo.reponame, maintainer_id=repo.maintainer_id)
    db.add(actual_repo)
    db.commit()
    db.refresh(actual_repo)
    return actual_repo

def get_repo_by_name(db,reponame):
    temp=db.query(Repository).filter(Repository.reponame==reponame).first()
    return temp


def get_repo_by_id(db,repo_id)
    temp=db.query(Repository).filter(Repository.repo_id==repo_id)
    return temp