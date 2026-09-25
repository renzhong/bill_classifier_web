from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select

from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.models.bill import BillTag
from app.models.category import Tag
from app.schemas.meta import TagIn, TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("")
async def list_tags(user: CurrentUser, session: SessionDep) -> dict:
    rows = (
        await session.scalars(select(Tag).where(Tag.user_id == user.id).order_by(Tag.id))
    ).all()
    return ok([TagOut.model_validate(r).model_dump() for r in rows])


@router.post("")
async def create_tag(body: TagIn, user: CurrentUser, session: SessionDep) -> dict:
    dup = await session.scalar(select(Tag).where(Tag.user_id == user.id, Tag.name == body.name))
    if dup:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "tag name already exists")
    tag = Tag(user_id=user.id, name=body.name, color=body.color)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return ok(TagOut.model_validate(tag).model_dump())


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, user: CurrentUser, session: SessionDep) -> dict:
    tag = await session.scalar(select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id))
    if not tag:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tag not found")
    used = await session.scalar(select(BillTag.bill_id).where(BillTag.tag_id == tag_id).limit(1))
    if used is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "tag is attached to bills")
    await session.execute(delete(Tag).where(Tag.id == tag_id))
    await session.commit()
    return ok({"deleted": tag_id})
