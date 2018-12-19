import os

from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

from model import Person


def initialize_database():
    """
    Creates the database and People table if they dont exist
    :return:
    """
    engine = create_engine(os.environ['DB_CONN_STRING'])

    # Create database
    if not database_exists(engine.url):
        create_database(engine.url)
        print('Successfully created DB')
    else:
        print('Database already exists')

    # Create people table
    if Person.__table__.exists(engine):
        print('People table already exists')
    else:
        Person.__table__.create(engine, checkfirst=True)
        print('Successfully created people table')


if __name__ == '__main__':
    initialize_database()
