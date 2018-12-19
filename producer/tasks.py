from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

app = Celery('fincompare', broker=os.environ['BROKER_CONN'])


@app.task(name='insert-person')
def insert_person_db(fullname: str, email: str):
    """
    Inserts a Person into the database with fullname and email
    This is a placeholder for the producer module to send tasks to the worker process
    :param fullname:
    :param email:
    :return:
    """
    raise NotImplementedError  # The task is implemented on the consumer server
