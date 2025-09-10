import threading
from typing import List

from sqlalchemy import Column, String, UnicodeText, func, distinct, Integer, BigInteger, Boolean

from DarkGod14Bot.modules.helper_funcs.msg_types import Types
from DarkGod14Bot.modules.sql import SESSION, BASE


class GitHub(BASE):
    __tablename__ = "github"
    chat_id = Column(
        String(14), primary_key=True
    )  # string because int is too large to be stored in a PSQL database.
    name = Column(UnicodeText, primary_key=True)
    value = Column(UnicodeText, nullable=False)
    backoffset = Column(Integer, nullable=False, default=0)

    def __init__(self, chat_id, name, value, backoffset):
        self.chat_id = str(chat_id)
        self.name = name
        self.value = value
        self.backoffset = backoffset

    def __repr__(self):
        return "<Git Repo %s>" % self.name


class MonitoredRepo(BASE):
    __tablename__ = "monitored_repos"
    
    chat_id = Column(String(14), primary_key=True)
    repo_name = Column(String(100), primary_key=True)
    repo_url = Column(String(200), nullable=False)
    last_commit_sha = Column(String(50), nullable=True)
    
    def __init__(self, chat_id, repo_name, repo_url, last_commit_sha=None):
        self.chat_id = chat_id
        self.repo_name = repo_name
        self.repo_url = repo_url
        self.last_commit_sha = last_commit_sha
        
    def __repr__(self):
        return f"<MonitoredRepo(chat_id='{self.chat_id}', repo_name='{self.repo_name}', repo_url='{self.repo_url}')>"


GitHub.__table__.create(checkfirst=True)
MonitoredRepo.__table__.create(checkfirst=True)

GIT_LOCK = threading.RLock()


def add_repo_to_db(chat_id, name, value, backoffset):
    with GIT_LOCK:
        prev = SESSION.query(GitHub).get((str(chat_id), name))
        if prev:
            SESSION.delete(prev)
        repo = GitHub(str(chat_id), name, value, backoffset)
        SESSION.add(repo)
        SESSION.commit()


def get_repo(chat_id, name):
    try:
        return SESSION.query(GitHub).get((str(chat_id), name))
    finally:
        SESSION.close()


def rm_repo(chat_id, name):
    with GIT_LOCK:
        repo = SESSION.query(GitHub).get((str(chat_id), name))
        if repo:
            SESSION.delete(repo)
            SESSION.commit()
            return True
        else:
            SESSION.close()
            return False


def get_all_repos(chat_id):
    try:
        return (
            SESSION.query(GitHub)
            .filter(GitHub.chat_id == str(chat_id))
            .order_by(GitHub.name.asc())
            .all()
        )
    finally:
        SESSION.close()



def add_monitored_repo(chat_id: str, repo_name: str, repo_url: str, last_commit_sha: str = None) -> bool:
    """Add a repository to monitoring"""
    try:
        existing = SESSION.query(MonitoredRepo).filter(
            MonitoredRepo.chat_id == chat_id,
            MonitoredRepo.repo_name == repo_name
        ).first()
        
        if existing:
            return False
            
        new_monitored = MonitoredRepo(chat_id, repo_name, repo_url, last_commit_sha)
        SESSION.add(new_monitored)
        SESSION.commit()
        return True
        
    except Exception as e:
        SESSION.rollback()
        print(f"Error adding monitored repo: {e}")
        return False
    finally:
        SESSION.close()


def remove_monitored_repo(chat_id: str, repo_name: str) -> bool:
    """Remove a repository from monitoring"""
    try:
        monitored = SESSION.query(MonitoredRepo).filter(
            MonitoredRepo.chat_id == chat_id,
            MonitoredRepo.repo_name == repo_name
        ).first()
        
        if monitored:
            SESSION.delete(monitored)
            SESSION.commit()
            return True
        return False
        
    except Exception as e:
        SESSION.rollback()
        print(f"Error removing monitored repo: {e}")
        return False
    finally:
        SESSION.close()


def get_monitored_repos_by_chat(chat_id: str) -> List[MonitoredRepo]:
    """Get all monitored repos from a specific chat"""
    try:
        return SESSION.query(MonitoredRepo).filter(
            MonitoredRepo.chat_id == chat_id
        ).all()
        
    except Exception as e:
        print(f"Error getting monitored repos by chat: {e}")
        return []
    finally:
        SESSION.close()


def get_all_monitored_repos() -> List[MonitoredRepo]:
    """Get all monitored repositories (for the verification process)"""
    try:
        return SESSION.query(MonitoredRepo).all()
        
    except Exception as e:
        print(f"Error getting all monitored repos: {e}")
        return []
    finally:
        SESSION.close()


def update_last_commit(chat_id: str, repo_name: str, commit_sha: str) -> bool:
    """Update the last known commit of a repository"""
    try:
        monitored = SESSION.query(MonitoredRepo).filter(
            MonitoredRepo.chat_id == chat_id,
            MonitoredRepo.repo_name == repo_name
        ).first()
        
        if monitored:
            monitored.last_commit_sha = commit_sha
            SESSION.commit()
            return True
        return False
        
    except Exception as e:
        SESSION.rollback()
        print(f"Error updating last commit: {e}")
        return False
    finally:
        SESSION.close()


def get_monitored_repo(chat_id: str, repo_name: str) -> MonitoredRepo:
    """Get a specific monitored repository"""
    try:
        return SESSION.query(MonitoredRepo).filter(
            MonitoredRepo.chat_id == chat_id,
            MonitoredRepo.repo_name == repo_name
        ).first()
        
    except Exception as e:
        print(f"Error getting specific monitored repo: {e}")
        return None
    finally:
        SESSION.close()


def cleanup_monitored_repos_for_chat(chat_id: str):
    """Clean all monitored repos from a chat (useful when bot is removed)"""
    try:
        SESSION.query(MonitoredRepo).filter(
            MonitoredRepo.chat_id == chat_id
        ).delete()
        SESSION.commit()
        
    except Exception as e:
        SESSION.rollback()
        print(f"Error cleaning monitored repos from chat {chat_id}: {e}")
    finally:
        SESSION.close()


def get_monitored_stats():
    """Get statistics of monitored repositories"""
    try:
        total_repos = SESSION.query(MonitoredRepo).count()
        total_chats = SESSION.query(MonitoredRepo.chat_id).distinct().count()
        
        return {
            'total_repos': total_repos,
            'total_chats': total_chats
        }
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {'total_repos': 0, 'total_chats': 0}
    finally:
        SESSION.close()