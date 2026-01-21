from fastapi import APIRouter

from app.modules.leads.schemas import LeadScoreRequest, LeadScoreResponse
from app.modules.leads.service import score_lead


router = APIRouter(tags=["leads"])


@router.post("/leads/score", response_model=LeadScoreResponse)
def lead_score(payload: LeadScoreRequest):
    r = score_lead(payload.text)
    return LeadScoreResponse(score=r.score, level=r.level, signals=r.signals, next_actions=r.next_actions, features=r.features)

