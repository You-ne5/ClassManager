from nextcord import Interaction
from aiosqlite import Cursor, Connection
import aiosqlite

async def get_db():
    db = await aiosqlite.connect("main.db")
    cursor = await db.cursor()

    return (db, cursor)

async def get_hac_id(guild_id: int, cursor: Cursor):  # hac = Help Archive Category
    HAC_id = await cursor.execute(
        "SELECT HelpArchiveCategoryID FROM Channels WHERE GuildID=?", (guild_id,)
    )
    HAC_id = await HAC_id.fetchone()
    HAC_id = HAC_id[0] if HAC_id else None
    return HAC_id


async def create_new_hac(interaction: Interaction):  # hac = Help Archive Category
    db, cursor = await get_db()
    req = await cursor.execute(
        "SELECT CategoryIndex FROM Channels WHERE GuildID=?", (interaction.guild.id,)
    )
    req = await req.fetchone()
    category_idx = req[0]
    new_hac = await interaction.guild.create_category(
        name=f"Help archive ({category_idx})"
    )

    await cursor.execute(
        "UPDATE Channels SET HelpArchiveCategoryID=?, CategoryIndex=? WHERE GuildID=?",
        (
            new_hac.id,
            category_idx + 1,
            interaction.guild.id,
        ),
    )
    await db.commit()

    return new_hac


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
