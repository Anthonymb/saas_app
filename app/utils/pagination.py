import math
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

async def paginate(db: AsyncSession, query: Select, page: int = 1, page_size: int = 20, response_schema=None) -> dict:
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    rows = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()
    items = [response_schema.model_validate(r) for r in rows] if response_schema else rows
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": math.ceil(total / page_size) if total else 1}
