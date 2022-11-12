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
        self.strict = False
    
    async def find(self, content: str) -> Optional[List[str]]:
        if content.startswith("https://") or content.startswith("http://"):
            return
        content = content.lower()
        exp = re.compile(r"[^a-zA-Zㄱ-ㅎㅏ-ㅣ가-힣]")
        removes = exp.findall(content)
        async for rem in self.async_list(removes):
            content = content.replace(rem, "")
        async for word in self.async_list(self.words):
            async for detection in self.async_list(self.words[word]):
                if detection in content:
                    return [word, detection]
                if self.strict is True:
                    w = re.compile(r"[a-zA-Zㄱ-ㅎㅏ-ㅣ가-힣]".join(detection))
                    result = w.findall(content)
                    if len(result) != 0:
                        return [word, detection]
        return None

    async def async_list(self, values: list) -> Any:
        for value in values:
            yield value
            await asyncio.sleep(0)
    
    async def cog_load(self) -> None:
        await self.prepare()

    async def prepare(self) -> None:
        await self.bot.wait_until_ready()
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
            webhook = disnake.Webhook.from_url(self.bot.config.webhook, session=cs, bot_token=self.bot.config.token)
            await webhook.send(f"Preparing: {category} categories and total {registered} words are registered.", username="로이드 포저", avatar_url=self.bot.user.display_avatar.url)
        o.close()

    @commands.Cog.listener("on_message")
    async def _detectWords(self, msg: disnake.Message) -> None:
        if msg.author.bot:
            return
        
        if msg.channel.type == disnake.ChannelType.private:
            return
        
        if msg.content.startswith("?add") or msg.content.startswith("?remove") or msg.content.startswith("?total"):
            return

        result = await self.find(msg.content)
        if not result:
            return
        
        async with aiohttp.ClientSession() as cs:
            webhook = disnake.Webhook.from_url(self.bot.config.webhook, session=cs, bot_token=self.bot.config.token)
            await webhook.send(f"""
Just found STRIKE from message.
Content : {msg.content}
Category : {result[0]}
Found : {result[1]}
            """, username="로이드 포저", avatar_url=self.bot.user.display_avatar.url)
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"INSERT INTO `counts` VALUES ('{result[0]}', '{msg.guild.id}', '{msg.author.id}')")
        o.close()
        await msg.channel.send(f"""
🌟 > {msg.author.mention}님이 카운트를 추가합니다!
감지된 스트라이크 : {result[0]}
        """)
    
    @commands.Cog.listener("on_member_remove")
    async def _removeData(self, member: disnake.Member) -> None:
        if member.bot:
            return

        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"DELETE FROM `counts` WHERE `user` = '{member.id}' AND `guild` = '{member.guild.id}'")
        o.close()

    @commands.command(name="strict")
    @commands.is_owner()
    async def _toggleStrict(self, ctx: commands.Context, toggle: bool) -> None:
        self.strict = toggle
        await ctx.reply(f"🌟 > 스트릭트 모드가 {toggle}로 변경되었습니다.")

    @commands.command(name="total")
    @commands.is_owner()
    async def _totalCounts(self, ctx: commands.Context, word: str) -> None:
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"SELECT * FROM `counts` WHERE `word` = '{word}' AND `guild` = '{ctx.guild.id}'")
        rows = await c.fetchall()
        if not rows:
            await ctx.reply(f"> 아직 {word} 스트라이크를 발견하지 못했습니다.")
        else:
            datas = {}
            async for row in self.async_list(rows):
                if row["user"] not in datas:
                    datas[row["user"]] = 1
                else:
                    datas[row["user"]] += 1
            content = ""
            async for d in self.async_list(datas):
                user = ctx.guild.get_member(int(d))
                if not user:
                    continue
                content += ""
            content += ""
            await ctx.reply(content)
        o.close()

    @commands.command(name="add")
    @commands.is_owner()
    async def _addWord(self, ctx: commands.Context, word: str, detect: str) -> None:
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"INSERT INTO `detects` VALUES ('{detect}', '{word}')")
        o.close()
#        await self.prepare()
        await ctx.reply("단어 추가에 성공했습니다! 변경 사항을 적용하려면 **?reload** 명령을 수행하세요.")
    
    @commands.command(name="remove")
    @commands.is_owner()
    async def _removeWord(self, ctx: commands.Context, detect: str) -> None:
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"DELETE FROM `detects` WHERE `detection` = '{detect}'")
        o.close()
#        await self.prepare()
        await ctx.reply("단어를 삭제했습니다! 변경 사항을 적용하려면 **?reload** 명령을 수행하세요.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Counter(bot))