from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging



# LOGGING
logger = logging.getLogger(__name__)

# DATABASE INSTANCE -- COMMIT 
async def database_commit(session: AsyncSession, instance):
    try:
        await session.commit()
        try:
            await session.refresh(instance)

        except Exception as refreshError:
            logger.warning(f"Refresh failed after commit: {refreshError}")

        return instance
    
    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Integrity ERROR: {e.orig}") # e.orig exact DB error batata hai
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entry creation failed")
    
    except SQLAlchemyError as e:
        await session.rollback()
        logger.exception(f"Database Transaction Failed")




# # DATABASE FETCH A TRANSACTION 
async def db_get_one(session: AsyncSession, statement):
    """Sirf data lata hai, koi exception raise nahi karta agar data na mile."""
    try:
        result = await session.scalars(statement)
        return result.one_or_none()
    except SQLAlchemyError:
        logger.exception("Database fetch failed")
        raise # Sirf DB crash par error dega
