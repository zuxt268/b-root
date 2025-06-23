from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any

# Type variable for domain entity
EntityType = TypeVar('EntityType')


class BaseService(Generic[EntityType], ABC):
    """Base service class to reduce code duplication across services."""
    
    # Common pagination limit
    LIMIT = 30
    
    def __init__(self, repository: Any):
        self.repository = repository
    
    def block_count(self) -> int:
        """Calculate number of pagination blocks."""
        return self.repository.count() // self.LIMIT + 1
    
    def find_all(self, page: int = 1) -> list[EntityType]:
        """Find all entities with pagination."""
        offset = (page - 1) * self.LIMIT
        return self.repository.find_all(limit=self.LIMIT, offset=offset)
    
    def find_by_id(self, entity_id: int) -> EntityType:
        """Find entity by ID or raise error."""
        entity = self.repository.find_by_id(entity_id)
        if entity is None:
            raise self._not_found_error(f"Entity with id {entity_id} not found")
        return entity
    
    @abstractmethod
    def _not_found_error(self, message: str) -> Exception:
        """Return appropriate not found error for this service."""
        pass