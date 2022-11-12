import asyncio
import re
from typing import Any, List, Optional

import aiohttp
import aiomysql
import disnake
from disnake.ext import commands

class Counter(commands.Cog, name="욕설 감지기"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    async def find(self, content: str) -> Optional[List[str]]:
        exp = re.compile(r"[^a-zA-Zㄱ-ㅎㅏ-ㅣ가-힣]")
        removes = exp.findall(content)
        async for rem in self.async_list(removes):
            content = content.replace(rem, "")
        async for word in self.async_list(self.words):
            async for detection in self.async_list(self.words["word"]):
                if detection in content:
                    return [word, detection]
                w = re.compile(".".join(detection))
                result = w.findall(content)
                if len(result) != 0:
                    return [word, detection]
        return None

    async def async_list(self, values: list) -> Any:
        for value in values:
            yield value
            await asyncio.sleep(0)
    
    async def cog_load(self) -> None:
        self.words = {} # {"ssibal": ["ssiba1", "sslbal"]...}
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute("SELECT * FROM `detects`")
        rows = await c.fetchall()
        registered = 0
        category = 0
        async for row in self.async_list(rows):
            if row["word"] not in self.words:
                self.words[row["word"]] = [row["detection"]]
                category += 1
            else:
                self.words[row["word"]].append(row["detection"])
            registered += 1
        async with aiohttp.ClientSession() as cs:
            webhook = disnake.Webhook(self.bot.config.webhook, session=cs, bot_token=self.bot.config.token)
            await webhook.send(f"Counter Preparing: {category} Categories, {registered} Words registered.")
        o.close()

    @commands.Cog.listener("on_message")
    async def _detectWords(self, msg: disnake.Message) -> None:
        if msg.author.bot:
            return
        
        if msg.channel.type == disnake.ChannelType.private:
            return
        
        result = await self.find(msg.content)
        if not result:
            return
        
        print(result)
        await msg.add_reaction("<:screaming:949665490060587098>")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Counter(bot))