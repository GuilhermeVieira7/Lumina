# ==========================================
# ROUTER: Diário de Observações (RF10)
# ==========================================

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session as DBSession

from auth import get_current_user
from database import get_db
from models import Note, Session, User
from permissions import get_profile_for, is_owner
from schemas import NoteCreate, NoteResponse

router = APIRouter(prefix="/api/notes", tags=["Diário"])


@router.get("/{profile_id}", response_model=List[NoteResponse])
def list_notes(
    profile_id: int,
    session_id: Optional[int] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Observações de responsáveis e profissionais, mais recentes primeiro."""
    get_profile_for(db, profile_id, current_user)
    query = db.query(Note).filter(Note.profile_id == profile_id)
    if session_id:
        query = query.filter(Note.session_id == session_id)
    return query.order_by(desc(Note.created_at), desc(Note.id)).limit(limit).all()


@router.post("", response_model=NoteResponse)
def create_note(
    data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Registrar uma observação, opcionalmente ligada a uma sessão."""
    profile = get_profile_for(db, data.profile_id, current_user)
    activity_type = None
    if data.session_id:
        session = db.query(Session).filter(
            Session.id == data.session_id, Session.profile_id == data.profile_id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        activity_type = session.activity_type

    role = "Responsável" if is_owner(profile, current_user) else "Profissional"
    note = Note(
        profile_id=data.profile_id,
        session_id=data.session_id,
        activity_type=activity_type,
        content=data.content.strip(),
        author=f"{current_user.username} ({role})",
        author_id=current_user.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}")
def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Apagar observação (quem escreveu ou o responsável)."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Observação não encontrada")
    profile = get_profile_for(db, note.profile_id, current_user)
    if note.author_id != current_user.id and not is_owner(profile, current_user):
        raise HTTPException(status_code=403, detail="Só quem escreveu ou o responsável pode apagar")
    db.delete(note)
    db.commit()
    return {"message": "Observação apagada"}
