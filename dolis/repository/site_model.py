from sqlalchemy import Column, Integer, String, Text, Index
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Sites(Base):
    __tablename__ = 'sites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    catchphrase = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    industry = Column(String(255), nullable=False)
    suggest = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index('ix_fulltext', 'title', 'catchphrase', 'description', 'industry', mysql_prefix='FULLTEXT'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'domain': self.domain,
            'catchphrase': self.catchphrase,
            'description': self.description,
            'industry': self.industry,
        }