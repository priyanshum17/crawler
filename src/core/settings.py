import json
from pydantic import BaseModel


class Config(BaseModel):
    """
    Configuration class for the application.
    """

    DB_PATH: str
    DB_LOCATION: str


configuration = Config(**json.load(open("config.json")))
