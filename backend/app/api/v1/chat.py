from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_company
from app.database.session import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.chat import ChatMessageOut
from app.schemas.prediction import ChatRequest, ChatResponse

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> ChatResponse:
    company = get_owned_company(company_id=payload.company_id, db=db, current_user=current_user)
    from app.services.chat_service import answer_question

    answer = answer_question(db, company, payload.message)
    return ChatResponse(answer=answer)


@router.get("/{company_id}/history", response_model=list[ChatMessageOut])
def history(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> list[ChatMessageOut]:
    from app.services.chat_service import get_history

    return [ChatMessageOut.model_validate(m) for m in get_history(db, company.id)]


@router.delete("/{company_id}/history")
def clear(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> dict:
    from app.services.chat_service import clear_history

    clear_history(db, company.id)
    return {"cleared": True}
