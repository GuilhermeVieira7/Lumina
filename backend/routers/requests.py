# ==========================================
# ROUTER: Prancha de Pedidos (comunicação da criança)
# ==========================================
# A criança toca num pedido (pausa, água, ajuda...), o Lumina fala a frase
# e registra o pedido para os adultos verem no diário e no relatório.

from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session as DBSession

from auth import get_current_user
from data.communication import REQUEST_OPTIONS, REQUESTS_BY_KEY, REWARD_OPTIONS
from database import get_db
from models import ChildRequest, User
from permissions import get_profile_for
from schemas import ChildRequestCreate, ChildRequestResponse

router = APIRouter(prefix="/api/requests", tags=["Prancha de Pedidos"])


def to_response(req: ChildRequest) -> ChildRequestResponse:
    option = REQUESTS_BY_KEY.get(req.key, {"icon": "💬", "label": req.key})
    return ChildRequestResponse(
        id=req.id, key=req.key, icon=option["icon"], label=option["label"],
        context=req.context, created_at=req.created_at,
    )


def summarize(requests) -> list:
    """Quantidade de cada pedido, do mais frequente para o menos frequente."""
    counts = Counter(r.key for r in requests)
    return [
        {"key": key, "icon": REQUESTS_BY_KEY.get(key, {}).get("icon", "💬"),
         "label": REQUESTS_BY_KEY.get(key, {}).get("label", key), "count": count}
        for key, count in counts.most_common()
    ]


@router.get("/options")
def list_options(current_user: User = Depends(get_current_user)):
    """Pedidos da prancha e prêmios sugeridos para o quadro de fichas."""
    return {"requests": REQUEST_OPTIONS, "rewards": REWARD_OPTIONS}


@router.post("", response_model=ChildRequestResponse)
def create_request(
    data: ChildRequestCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    get_profile_for(db, data.profile_id, current_user)
    if data.key not in REQUESTS_BY_KEY:
        raise HTTPException(status_code=400, detail="Pedido desconhecido")
    req = ChildRequest(profile_id=data.profile_id, key=data.key, context=(data.context or "").strip() or None)
    db.add(req)
    db.commit()
    db.refresh(req)
    return to_response(req)


@router.get("/{profile_id}")
def list_requests(
    profile_id: int,
    days: Optional[int] = None,
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Pedidos recentes e a contagem por tipo no período."""
    get_profile_for(db, profile_id, current_user)
    query = db.query(ChildRequest).filter(ChildRequest.profile_id == profile_id)
    if days:
        query = query.filter(ChildRequest.created_at >= datetime.utcnow() - timedelta(days=days))
    everything = query.order_by(desc(ChildRequest.created_at), desc(ChildRequest.id)).all()
    return {
        "total": len(everything),
        "summary": summarize(everything),
        "items": [to_response(r) for r in everything[:max(1, min(limit, 100))]],
    }
