from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

# Type variables for generic repository
ModelType = TypeVar('ModelType')
DomainType = TypeVar('DomainType')


class BaseRepository(Generic[ModelType, DomainType], ABC):
    """Base repository class to reduce code duplication across repositories."""
    
    def __init__(self, session: Session):
        self.session = session
    
    @property
    @abstractmethod
    def model_class(self) -> type[ModelType]:
        """Return the SQLAlchemy model class."""
        pass
    
    @abstractmethod
    def to_domain(self, model: ModelType) -> DomainType:
        """Convert model to domain object."""
        pass
    
    @abstractmethod
    def to_model(self, domain: DomainType) -> dict:
        """Convert domain object to model data."""
        pass
    
    def _get(self, _id: int) -> Optional[ModelType]:
        """Private method to get model by ID."""
        return self.session.query(self.model_class).filter(self.model_class.id == _id).first()
    
    def find_by_id(self, _id: int) -> Optional[DomainType]:
        """Find domain object by ID."""
        record = self._get(_id)
        if record is not None:
            return self.to_domain(record)
        return None
    
    def add(self, entity: DomainType) -> DomainType:
        """Add new entity to repository."""
        model_data = self.to_model(entity)
        record = self.model_class(**model_data)
        self.session.add(record)
        return self.to_domain(record)
    
    def count(self) -> int:
        """Count total records."""
        return self.session.query(func.count(self.model_class.id)).scalar()
    
    def find_all(self, limit: int = 30, offset: int = 0) -> List[DomainType]:
        """Find all entities with pagination."""
        records = (self.session.query(self.model_class)
                  .limit(limit)
                  .offset(offset)
                  .all())
        return [self.to_domain(record) for record in records]