import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class UnitOfWork:
    def __init__(self):
        db_user = os.getenv('DATABASE_USER')
        db_password = os.getenv('DATABASE_PASSWORD')
        db_host = os.getenv('DATABASE_HOST')
        db_scheme = os.getenv('DATABASE_SCHEME')
        
        if not all([db_user, db_password, db_host, db_scheme]):
            raise ValueError("Database connection parameters are not properly configured")
        
        connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_scheme}"
        self.session_maker = sessionmaker(
            bind=create_engine(
                connection_string, pool_size=5, max_overflow=10, pool_recycle=3600
            )
        )

    def __enter__(self):
        self.session = self.session_maker()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.session.rollback()
        finally:
            self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
