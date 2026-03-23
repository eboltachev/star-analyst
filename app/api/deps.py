from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    uid = request.session.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return user
