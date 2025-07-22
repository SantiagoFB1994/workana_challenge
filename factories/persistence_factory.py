from typing import Literal
from persistence.postgres_handler import PostgresHandler
from persistence.csv_handler import CSVHandler
from persistence.base_persistence import BasePersistence

PersistenceType = Literal['postgres', 'csv']

class PersistenceFactory:
    @staticmethod
    def create_persistence(p_type: PersistenceType) -> BasePersistence:
        """
        Create a persitence instance with the specified type

        Args:
            p_type: persistence type ('postgres' or 'csv')
            
        Returns:
            BasePersistence instance
            
        Raises:
            ValueError: If type is not supported
        """
        implementations = {
            'postgres': PostgresHandler,
            'csv': CSVHandler
        }
        
        if p_type not in implementations:
            raise ValueError(
                f"Persistence type is not supported: {p_type}. "
                f"Valid options: {list(implementations.keys())}"
            )
            
        return implementations[p_type]()