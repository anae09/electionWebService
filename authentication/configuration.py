from datetime import timedelta
import os

db = os.environ["DATABASE_URL"];


class Configuration:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@{}/authentication".format(db);
    JWT_SECRET_KEY = "ANA_ANA_ANA";
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1);
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30);
