from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select

from app.ai.base import ProviderError
from app.ai.registry import list_providers
from app.ai.service import render_preview, test_classify
from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.core.security import encrypt_secret
from app.models.ai import AiCredential, AiStrategy
from app.models.category import Category
from app.schemas.ai import (
    AiCredentialIn,
    AiCredentialOut,
    AiCredentialPatchIn,
    AiStrategyIn,
    AiStrategyOut,
    AiStrategyPatchIn,
    PreviewIn,
    PreviewOut,
    ProviderMetaOut,
    TestIn,
    TestOut,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/providers")
async def providers_endpoint() -> dict:
    return ok([ProviderMetaOut(**p).model_dump() for p in list_providers()])


# ===== credentials =====


@router.get("/credentials")
async def list_credentials(user: CurrentUser, session: SessionDep) -> dict:
    rows = (
        await session.scalars(
            select(AiCredential).where(AiCredential.user_id == user.id).order_by(AiCredential.id)
        )
    ).all()
    return ok([AiCredentialOut.model_validate(r).model_dump(mode="json") for r in rows])


@router.post("/credentials")
async def create_credential(body: AiCredentialIn, user: CurrentUser, session: SessionDep) -> dict:
    cred = AiCredential(
        user_id=user.id,
        provider=body.provider,
        model_name=body.model_name,
        api_key_encrypted=encrypt_secret(body.api_key),
        base_url=body.base_url,
        enabled=body.enabled,
    )
    session.add(cred)
    await session.commit()
    await session.refresh(cred)
    return ok(AiCredentialOut.model_validate(cred).model_dump(mode="json"))


@router.patch("/credentials/{cred_id}")
async def patch_credential(
    cred_id: int, body: AiCredentialPatchIn, user: CurrentUser, session: SessionDep
) -> dict:
    cred = await session.scalar(
        select(AiCredential).where(AiCredential.id == cred_id, AiCredential.user_id == user.id)
    )
    if not cred:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "credential not found")
    data = body.model_dump(exclude_unset=True)
    if "api_key" in data and data["api_key"]:
        cred.api_key_encrypted = encrypt_secret(data.pop("api_key"))
    elif "api_key" in data:
        data.pop("api_key")
    for k, v in data.items():
        setattr(cred, k, v)
    await session.commit()
    await session.refresh(cred)
    return ok(AiCredentialOut.model_validate(cred).model_dump(mode="json"))


@router.delete("/credentials/{cred_id}")
async def delete_credential(cred_id: int, user: CurrentUser, session: SessionDep) -> dict:
    cred = await session.scalar(
        select(AiCredential).where(AiCredential.id == cred_id, AiCredential.user_id == user.id)
    )
    if not cred:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "credential not found")
    # 解绑相关 strategy
    strategies = (
        await session.scalars(
            select(AiStrategy).where(
                AiStrategy.user_id == user.id, AiStrategy.credential_id == cred_id
            )
        )
    ).all()
    for s in strategies:
        s.credential_id = None
        s.active = False
    await session.execute(delete(AiCredential).where(AiCredential.id == cred_id))
    await session.commit()
    return ok({"deleted": cred_id, "unbound_strategies": len(strategies)})


# ===== strategies =====


@router.get("/strategies")
async def list_strategies(user: CurrentUser, session: SessionDep) -> dict:
    rows = (
        await session.scalars(
            select(AiStrategy).where(AiStrategy.user_id == user.id).order_by(AiStrategy.id)
        )
    ).all()
    return ok([AiStrategyOut.model_validate(r).model_dump(mode="json") for r in rows])


@router.post("/strategies")
async def create_strategy(body: AiStrategyIn, user: CurrentUser, session: SessionDep) -> dict:
    if body.credential_id is not None:
        cred = await session.scalar(
            select(AiCredential).where(
                AiCredential.id == body.credential_id, AiCredential.user_id == user.id
            )
        )
        if not cred:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "credential not found")
    s = AiStrategy(user_id=user.id, **body.model_dump())
    session.add(s)
    await session.commit()
    await session.refresh(s)
    return ok(AiStrategyOut.model_validate(s).model_dump(mode="json"))


@router.patch("/strategies/{sid}")
async def patch_strategy(
    sid: int, body: AiStrategyPatchIn, user: CurrentUser, session: SessionDep
) -> dict:
    s = await session.scalar(
        select(AiStrategy).where(AiStrategy.id == sid, AiStrategy.user_id == user.id)
    )
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "strategy not found")
    data = body.model_dump(exclude_unset=True)
    if "credential_id" in data and data["credential_id"] is not None:
        cred = await session.scalar(
            select(AiCredential).where(
                AiCredential.id == data["credential_id"], AiCredential.user_id == user.id
            )
        )
        if not cred:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "credential not found")
    for k, v in data.items():
        setattr(s, k, v)
    await session.commit()
    await session.refresh(s)
    return ok(AiStrategyOut.model_validate(s).model_dump(mode="json"))


@router.delete("/strategies/{sid}")
async def delete_strategy(sid: int, user: CurrentUser, session: SessionDep) -> dict:
    s = await session.scalar(
        select(AiStrategy).where(AiStrategy.id == sid, AiStrategy.user_id == user.id)
    )
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "strategy not found")
    await session.execute(delete(AiStrategy).where(AiStrategy.id == sid))
    await session.commit()
    return ok({"deleted": sid})


# ===== preview + test =====


@router.post("/strategies/preview")
async def preview_endpoint(body: PreviewIn, user: CurrentUser, session: SessionDep) -> dict:
    cats = (await session.scalars(select(Category).where(Category.user_id == user.id))).all()
    prompt = render_preview(body.strategy_text, [c.name for c in cats])
    return ok(PreviewOut(prompt=prompt).model_dump())


@router.post("/test")
async def test_endpoint(body: TestIn, user: CurrentUser, session: SessionDep) -> dict:
    try:
        res = await test_classify(
            session,
            user_id=user.id,
            credential_id=body.credential_id,
            strategy_id=body.strategy_id,
            sample=body.sample,
        )
    except ProviderError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    return ok(
        TestOut(
            category=res.category,
            confidence=str(res.confidence) if res.confidence is not None else None,
            raw=res.raw,
        ).model_dump()
    )
