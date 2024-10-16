from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from repository.site_model import Sites


class SiteRepository:
    def __init__(self, session: Session):
        self.session = session

    def partial_match(self, search_query) -> list:
        print("partial_match")
        query = """
            SELECT id 
            FROM sites
            WHERE (title LIKE :search_query
               OR catchphrase LIKE :search_query
               OR description LIKE :search_query
               OR industry LIKE :search_query)
            AND suggest != -1   
            ORDER BY suggest DESC, id DESC  
            LIMIT 10;
        """
        search_query_with_wildcards = f"%{search_query}%"
        record = self.session.execute(text(query), {'search_query': search_query_with_wildcards})
        results = []
        for row in record.fetchall():
            site: Sites = self.session.query(Sites).get(row[0])
            result = site.to_dict()
            results.append(result)
        return results

    def full_text_search(self, search_query) -> list:
        print("full_text_search")
        query = """
        SELECT id, MATCH (title, catchphrase, description, industry) 
           AGAINST (:search_query IN NATURAL LANGUAGE MODE) AS score FROM sites
        WHERE MATCH (title, catchphrase, description, industry)
        AGAINST (:search_query IN NATURAL LANGUAGE MODE)
        AND suggest != -1
        ORDER BY score, suggest DESC, id DESC
        LIMIT 10
        """
        record = self.session.execute(text(query), {'search_query': search_query})
        results = []
        for row in record.fetchall():
            site: Sites = self.session.query(Sites).get(row[0])
            result = site.to_dict()
            result["score"] = row[1]
            results.append(result)
        return results

    def find_all_domain(self) -> list[str]:
        results = self.session.query(Sites).with_entities(Sites.domain).all()
        return [str(result[0]) for result in results]

    def find_by_domain(self, domain) -> Optional[Sites]:
        return self.session.query(Sites).filter(Sites.domain.like(f"%{domain}%")).first()

    def update_suggest_status(self, _id, suggest: int):
        return self.session.query(Sites).filter(Sites.id == _id).update({'suggest': suggest})

    def increment_suggest_score(self, _id):
        self.session.query(Sites).filter(Sites.id == _id).update({'suggest': Sites.suggest+1})

    def insert(self, row):
        site = Sites()
        site.domain = row[0]
        site.title = row[1]
        site.catchphrase = row[2]
        site.description = row[3]
        site.industry = row[4]
        try:
            self.session.add(site)
        except IntegrityError:
            self.session.rollback()
