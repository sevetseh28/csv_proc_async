from __future__ import absolute_import, unicode_literals

import os

from celery import Celery, Task
from celery.utils.log import get_task_logger
from database.model import Person
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

app = Celery('fincompare', broker=os.environ['BROKER_CONN'])
logger = get_task_logger(__name__)


class DBTask(Task):
    """
    This is a custom task class so that each worker can have its own session to the database
    """
    _session = None

    @property
    def session(self):
        if self._session is None:
            self._session = self.__get_engine_session()
        return self._session

    def __get_engine_session(self):
        self.engine = create_engine(os.environ['DB_CONN_STRING'])
        Session = sessionmaker(bind=self.engine)
        return Session()


@app.task(base=DBTask, bind=True, name='insert-person')
def insert_person_db(self, fullname: str, email: str):
    """
    Inserts a Person into the database with fullname and email
    :param fullname:
    :param email:
    :return:
    """
    person = Person(fullname=fullname, email=email)
    self.session.add(person)
    try:
        self.session.commit()
        logger.info(f'Commited into DB! Fullname: {fullname} - Email: {email}')
    except IntegrityError:
        logger.error(f'Email already exists in DB: {email}')
        self.session.rollback()
