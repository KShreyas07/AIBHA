import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_owned_company
from app.database.session import get_db
from app.models.company import Company
from app.schemas.goal import GoalCreate, GoalOut
from app.services.goal_service import create_goal, delete_goal, list_goals

router = APIRouter()


@router.post("/{company_id}", response_model=GoalOut)
def create(
    payload: GoalCreate,
    company: Company = Depends(get_owned_company),
    db: Session = Depends(get_db),
) -> GoalOut:
    try:
        goal = create_goal(db, company, payload.label, payload.metric, payload.target_value, payload.target_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Re-read through list_goals so the freshly-created goal comes back with the same
    # computed progress/on-track fields every other goal in the list has.
    goals = list_goals(db, company.id)
    return GoalOut.model_validate(next(g for g in goals if g["id"] == goal.id))


@router.get("/{company_id}", response_model=list[GoalOut])
def list_for_company(company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> list[GoalOut]:
    return [GoalOut.model_validate(g) for g in list_goals(db, company.id)]


@router.delete("/{company_id}/{goal_id}")
def delete(goal_id: uuid.UUID, company: Company = Depends(get_owned_company), db: Session = Depends(get_db)) -> dict:
    if not delete_goal(db, company.id, goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"deleted": True}
