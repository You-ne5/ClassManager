from nextcord import Message, Interaction
import validators
from utils.db import DB

async def get_hac_id(guild_id: int):  # hac = Help Archive Category

    db = DB()
    await db.load_db("main.db")

    HAC_id = await db.get_fetchone(
        "SELECT HelpArchiveCategoryID FROM GuildsConstants WHERE GuildID=?", (guild_id,)
    )
    HAC_id = HAC_id[0] if HAC_id else None
    return HAC_id


async def get_help_category_id(guild_id: int) -> int | None:

    db = DB()
    await db.load_db("main.db")

    help_category_id = await db.get_fetchone(
        "SELECT HelpCategoryId FROM GuildsConstants WHERE GuildId=?", (guild_id,)
    )
    help_category_id = help_category_id[0] if help_category_id else None
    return help_category_id


async def get_lessons_category_id(guild_id: int): 

    db = DB()
    await db.load_db("main.db")

    lessons_category_id = await db.get_fetchone(
        "SELECT LessonsCategoryId FROM GuildsConstants WHERE GuildID=?", (guild_id,)
    )
    lessons_category_id = lessons_category_id[0] if lessons_category_id else None
    return lessons_category_id


async def get_exo_channel_id(guild_id: int): 

    db = DB()
    await db.load_db("main.db")

    exo_channel_id = await db.get_fetchone(
        "SELECT ExoChannelId FROM GuildsConstants WHERE GuildID=?", (guild_id,)
    )
    exo_channel_id = exo_channel_id[0] if exo_channel_id else None
    return exo_channel_id


async def get_announce_channel_id(guild_id: int): 

    db = DB()
    await db.load_db("main.db")

    announce_channel_id = await db.get_fetchone(
        "SELECT AnnounceChannelId FROM GuildsConstants WHERE GuildID=?", (guild_id,)
    )
    announce_channel_id = announce_channel_id[0] if announce_channel_id else None
    return announce_channel_id


async def create_constant(interaction : Interaction, constant_name_in_db : str) -> None:
    db = DB()
    await db.load_db("main.db")

    print(constant_name_in_db)

    if "category" in constant_name_in_db.lower():
        category_name = "help" if constant_name_in_db == "HelpCategoryId" else "help archive" if constant_name_in_db == "HelpArchiveCategoryId" else "Lessons" if constant_name_in_db == "LessonsCategoryId" else "Validation"
        created_constant = await interaction.guild.create_category(name=category_name)

    elif "channel" in constant_name_in_db.lower():
        channel_name = "📝exercices" if constant_name_in_db == "ExoChannelId" else "📢annonces" if constant_name_in_db == "AnnounceChannelId" else "unnamed channel"
        created_constant = await interaction.guild.create_text_channel(name=channel_name)
    
    elif "role" in constant_name_in_db.lower():
        role_name = "Student role" if constant_name_in_db == "StudentRoleId" else "unnamed role"
        created_constant = await interaction.guild.create_role(name=role_name)

    await db.request(f"UPDATE GuildsConstants SET {constant_name_in_db}=? WHERE GuildId=?", (created_constant.id, interaction.guild_id))


def message_verif(message : Message) -> bool:
    content = message.content
    contains_link = any(validators.url(ele) for ele in content.split()) and "https://tenor.com" not in content
    return bool(bool(message.attachments) or contains_link)

def pgcd(a, b):

    while True:
        if a % b == 0:
            return abs(b)
        else:
            rest = a % b
            a = b
            b = rest


def ppcm(a, b):
    (a, b) = (a, b) if a > b else (b, a)
    k = 1
    while True:
        if (a * k) % b == 0:
            return a * k
        k += 1


def eq_2(a, b, c):
    d = pgcd(a, b)
    if c % d != 0:

        return None

    a //= d
    b //= d
    c //= d

    def special_solution(a, b, c):
        for m in range(1000):
            for i in [-1, 1]:

                x = i * m
                for z in range(1000):
                    for j in [-1, 1]:
                        if z == 0 and j == 1:
                            continue

                        y = j * z
                        if a * x + b * y == c:
                            return (x, y)

    s_c = special_solution(a, b, c)
    if not s_c:
        return "not found brother"

    x0, y0 = s_c

    def sign(n: int):
        return "+" if n > 0 else "-"

    x = f"{b}k{f' {sign(x0)} {abs(x0)}' if x0 else ''}"
    y = f"{-a}k{f' {sign(y0)} {abs(y0)}' if y0 else ''}"

    return (x, y)
