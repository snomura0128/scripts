import json
import os
import sqlalchemy.ext.declarative
from sqlalchemy import create_engine
from sqlalchemy.schema import Column
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy.types import Integer, String, SmallInteger, TIME, FLOAT, TIMESTAMP
from sqlalchemy.orm import sessionmaker

Base = sqlalchemy.ext.declarative.declarative_base()


class TimelyOdds(Base):
    __tablename__ = "timely_odds"
    id = Column(Integer, primary_key=True)
    held = Column(String(20))
    race_number = Column(SmallInteger)
    horse_number = Column(SmallInteger)
    acquisition_time = Column(TIME)
    start_time = Column(TIME)
    odds = Column(FLOAT)
    popular = Column(SmallInteger)
    horse_name = Column(String(20))
    insert_time = Column(TIMESTAMP, server_default=current_timestamp())


class Repository:

    def __init__(self):
        # 設定ファイルから接続情報を取得する。
        json_file = open(os.path.dirname(__file__) + '/settings.json', 'r')
        json_data = json.load(json_file)
        user = json_data["user"]
        password = json_data["password"]
        host = json_data["host"]
        db = json_data["db"]
        port = json_data["port"]
        charset = json_data["charset"]
        self.engine = create_engine(f"mysql://{user}:{password}@{host}:{port}/{db}?charset={charset}")
        SessionClass = sessionmaker(self.engine)
        self.__session = SessionClass()

    def insert(self, record):
        self.__session.add(record)

    def commit(self):
        self.__session.commit()
