from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select

from app.classify.strategy_types import REGISTRY, registered_types
from app.classify.strategy_types.ai_classify import AiClassifyStrategy
from app.core.deps import CurrentUser, SessionDep
from app.core.response import ok
from app.models.pipeline import PipelineStep
from app.schemas.pipeline import (
    PipelineStepIn,
    PipelineStepOut,
    PipelineStepPatchIn,
    ReorderIn,
    StrategyTypeMeta,
)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/strategy-types")
async def list_strategy_types() -> dict:
    return ok([StrategyTypeMeta(**s.metadata()).model_dump() for s in registered_types()])


@router.get("/steps")
async def list_steps(user: CurrentUser, session: SessionDep) -> dict:
    rows = (
        await session.scalars(
            select(PipelineStep)
            .where(PipelineStep.user_id == user.id)
            .order_by(PipelineStep.sort_order, PipelineStep.id)
        )
    ).all()
    return ok([PipelineStepOut.model_validate(r).model_dump() for r in rows])


async def _validate_params(strategy_type: str, params: dict, *, session, user_id: int) -> None:
    s = REGISTRY.get(strategy_type)
    if not s:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown strategy_type: {strategy_type}")
    try:
        s.validate_params(params)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    # AiClassifyStrategy 还要校验 strategy_id 是否属于当前用户
    if isinstance(s, AiClassifyStrategy):
        try:
            await s.validate_params_with_session(params, session=session, user_id=user_id)
        except ValueError as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e


@router.post("/steps")
async def create_step(body: PipelineStepIn, user: CurrentUser, session: SessionDep) -> dict:
    await _validate_params(body.strategy_type, body.params, session=session, user_id=user.id)
    step = PipelineStep(user_id=user.id, **body.model_dump())
    session.add(step)
    await session.commit()
    await session.refresh(step)
    return ok(PipelineStepOut.model_validate(step).model_dump())


@router.patch("/steps/{step_id}")
async def patch_step(
    step_id: int, body: PipelineStepPatchIn, user: CurrentUser, session: SessionDep
) -> dict:
    step = await session.scalar(
        select(PipelineStep).where(PipelineStep.id == step_id, PipelineStep.user_id == user.id)
    )
    if not step:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "step not found")
    data = body.model_dump(exclude_unset=True)
    if "params" in data:
        await _validate_params(step.strategy_type, data["params"], session=session, user_id=user.id)
    for k, v in data.items():
        setattr(step, k, v)
    await session.commit()
    await session.refresh(step)
    return ok(PipelineStepOut.model_validate(step).model_dump())


@router.delete("/steps/{step_id}")
async def delete_step(step_id: int, user: CurrentUser, session: SessionDep) -> dict:
    step = await session.scalar(
        select(PipelineStep).where(PipelineStep.id == step_id, PipelineStep.user_id == user.id)
    )
    if not step:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "step not found")
    await session.execute(delete(PipelineStep).where(PipelineStep.id == step_id))
    await session.commit()
    return ok({"deleted": step_id})


@router.post("/steps/reorder")
async def reorder(body: ReorderIn, user: CurrentUser, session: SessionDep) -> dict:
    for entry in body.order:
        sid = int(entry.get("id", 0))
        sort = int(entry.get("sort_order", 0))
        step = await session.scalar(
            select(PipelineStep).where(PipelineStep.id == sid, PipelineStep.user_id == user.id)
        )
        if step:
            step.sort_order = sort
    await session.commit()
    return ok({"reordered": len(body.order)})
