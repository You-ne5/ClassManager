from aiosqlite import connect

class DB:
    def __init__(self) -> None:
        return
    
    async def load_db(self, path):
        self.conn = await connect(path)
        self.curr = await self.conn.cursor()

        
        await self.curr.execute("""CREATE TABLE IF NOT EXISTS HelpChannels(
                        GuildId INTERGER NOT NULL,
                        ChannelId INTERGER NOT NULL,
                        AuthorId INTERGER NOT NULL
        )""")

        await self.curr.execute("""CREATE TABLE IF NOT EXISTS GuildsConstants(
                        GuildId INTERGER NOT NULL,
                        HelpCategoryId INTERGER,
                        HelpArchiveCategoryID INTERGER,
                        LessonsCategoryId INTERGER,
                        ExoChannelId INTERGER,
                        AnnounceChannelId INTERGER
        )""")
        
    async def request(self, req: str, args: tuple = None):
        res =  await self.curr.execute(req, args)
        await self.conn.commit()
        return res
    
    async def get_fetchone(self, req: str, args: tuple = None):
        res =  await self.curr.execute(req, args)
        return await res.fetchone()
    
    async def get_fetchall(self, req: str, args: tuple = None):
        res =  await self.curr.execute(req, args)
        return await res.fetchall()
