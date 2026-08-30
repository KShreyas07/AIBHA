from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.prediction import ChatRequest, ChatResponse
from app.api.deps import get_owned_company

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> ChatResponse:
    company = get_owned_company(company_id=payload.company_id, db=db, current_user=current_user)
    from app.services.chat_service import answer_question

    answer = answer_question(db, company, payload.message)
    return ChatResponse(answer=answer)
