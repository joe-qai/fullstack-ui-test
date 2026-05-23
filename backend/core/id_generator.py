import re
from sqlalchemy.orm import Session


def next_id(prefix: str, model_class, db: Session) -> str:
    last = db.query(model_class).order_by(model_class.id.desc()).first()
    if last and last.id.startswith(prefix):
        m = re.search(rf'{re.escape(prefix)}(\d+)$', last.id)
        if m:
            return f"{prefix}{int(m.group(1)) + 1}"
    return f"{prefix}1"
