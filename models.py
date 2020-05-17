from pony.orm import Database, Required, Json
from vk_bot.settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)

class UserState(db.Entity):
    """
    Userstate during scenario execution
    """
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)

class Registration(db.Entity):
    """
    Registration information
    """
    name = Required(str)
    email = Required(str)

db.generate_mapping(create_tables=True)