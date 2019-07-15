from sqlalchemy import create_engine, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from model_buyer.exceptions.exceptions import NoResultFoundException


class Database:
    base = declarative_base()

    def __init__(self, config):
        self.engine = create_engine(config["DB_ENGINE"],
                                    connect_args={'check_same_thread': False})
        Database.base.metadata.create_all(self.engine)
        DbEntity.data_base = self

    def get_session(self):
        return sessionmaker(bind=self.engine)()

    def rollback(self):
        self.get_session().rollback()


class DbEntity(Database.base):
    __abstract__ = True
    data_base = None

    def delete(self):
        session = DbEntity.data_base.get_session()
        current_db_sessions = session.object_session(self)
        if current_db_sessions:
            current_db_sessions.delete(self)
            current_db_sessions.commit()
        else:
            session.delete(self)
            session.commit()

    def save(self):
        session = DbEntity.data_base.get_session()
        current_db_sessions = session.object_session(self)
        if current_db_sessions:
            current_db_sessions.add(self)
            current_db_sessions.commit()
        else:
            session.add(self)
            session.commit()

    @classmethod
    def query(cls, entity, filters, all=False):
        if not filters:
            return DbEntity.data_base.get_session().query(entity).all()
        query_result = DbEntity.data_base.get_session().query(entity).filter_by(**filters)
        result = query_result.all() if all else query_result.first()
        if not result:
            raise NoResultFoundException(filters)
        return result

    def update(self, entity, filters, update_data):
        session = DbEntity.data_base.get_session()
        current_db_sessions = session.object_session(self)
        if current_db_sessions:
            current_db_sessions.query(entity).filter_by(**filters).update(update_data,synchronize_session=False)
            current_db_sessions.commit()
        else:
            session.query(entity).filter_by(**filters).update(update_data,synchronize_session=False)
            session.commit()


