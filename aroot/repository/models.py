from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
)
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class AdminUsersModel(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)

    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
        }


class CustomersModel(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    wordpress_url = Column(String(255), nullable=False)
    facebook_token = Column(String(255))
    start_date = Column(DateTime)
    instagram_business_account_id = Column(String(255))
    instagram_business_account_name = Column(String(255))
    instagram_token_status = Column(
        Integer, nullable=False, default=0
    )  # Changed to SmallInteger
    delete_hash = Column(Boolean, default=False)
    payment_type = Column(String(255), nullable=False)

    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "wordpress_url": self.wordpress_url,
            "facebook_token": self.facebook_token,
            "start_date": self.start_date,
            "instagram_business_account_id": self.instagram_business_account_id,
            "instagram_business_account_name": self.instagram_business_account_name,
            "instagram_token_status": self.instagram_token_status,
            "delete_hash": self.delete_hash,
            "payment_type": self.payment_type,
        }


class PostsModel(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    media_id = Column(String(45), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    timestamp = Column(String(45))
    media_url = Column(Text)
    created_at = Column(DateTime)
    permalink = Column(String(255))
    wordpress_link = Column(String(255))

    def dict(self):
        return {
            "id": self.id,
            "media_id": self.media_id,
            "customer_id": self.customer_id,
            "timestamp": self.timestamp,
            "media_url": self.media_url,
            "created_at": self.created_at,
            "permalink": self.permalink,
            "wordpress_link": self.wordpress_link,
        }
