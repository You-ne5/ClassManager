from utils.db import DB

async def get_constant_id(guild_id: int, constant_name_in_db : str):

    db = DB()
    await db.load_db("main.db")

    constant_id = await db.get_fetchone(
        f"SELECT {constant_name_in_db} FROM GuildsConstants WHERE GuildID=?", (guild_id,)
    )
    constant_id = constant_id[0] if constant_id else None
    return constant_id