import asyncio
import io
import time
import re
from typing import Any, List, Optional

import aiohttp
import aiomysql
import disnake
from disnake.ext import commands

class Counter(commands.Cog, name="욕설 감지기"):
    class View(disnake.ui.View):
        class Strict(disnake.ui.View):
            class StrictSelect(disnake.ui.StringSelect):
                def __init__(self, data: dict) -> None:
                    texts = ["꺼짐", "간단", "보통", "엄격"]
                    super().__init__(
                        placeholder=f"새로운 감지 모드를 지정해주세요. 현재 '{texts[int(data['mode'])]}'",
                        min_values=1,
                        max_values=1,
                        options=[
                            disnake.SelectOption(label="꺼짐", value="0", description="로이드가 더 이상 스트라이크를 감지하지 않습니다.", emoji="🚫"),
                            disnake.SelectOption(label="간단", value="1", description="스트라이크를 정확히 포함하는 경우에만 감지합니다.", emoji="❓"),
                            disnake.SelectOption(label="보통", value="2", description="스트라이크 내부 혹은 주변에 특수문자 및 숫자가 있는 경우에는 감지합니다.", emoji="❗"),
                            disnake.SelectOption(label="엄격", value="3", description="스트라이크 내부 혹은 주변에 어떠한 문자가 있더라도 감지합니다.", emoji="‼️")
                        ],
                        disabled=False,
                        row=0
                    )
                
                async def callback(self, inter: disnake.MessageInteraction) -> None:
                    o = await aiomysql.connect(**inter.bot.config.mysql)
                    c = await o.cursor(aiomysql.DictCursor)
                    await c.execute(f"UPDATE `settings` SET `mode` = '{self.values[0]}' WHERE `guild` = '{inter.guild.id}'")
                    o.close()
                    await inter.response.edit_message(content=f"> {str(self.options[int(self.values[0])].emoji)} 설정 완료! 이제 감지 모드는 `{self.options[int(self.values[0])].label}`입니다.", view=None)
                    self.view.stop()


            def __init__(self, inter: disnake.ApplicationCommandInteraction, data: dict) -> None:
                super().__init__(timeout=30)
                self.inter = inter
                self.data = data
                self.add_item(self.StrictSelect(data))
            
            async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
                return self.inter.author == inter.author
            
            async def on_timeout(self) -> None:
                await self.inter.delete_original_message()

            @disnake.ui.button(
                label="취소하기",
                style=disnake.ButtonStyle.red,
                emoji="🆖",
                disabled=False,
                row=1
            )
            async def _cancel(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
                await inter.response.pong()
                await self.inter.delete_original_message()
                self.stop()
        

        class Respond(disnake.ui.View):
            class RespondSelect(disnake.ui.StringSelect):
                def __init__(self, data: dict) -> None:
                    texts = ["매너 모드", "약하게", "적당하게", "시끄럽게"]
                    super().__init__(
                        placeholder=f"새로운 응답 유형을 지정해주세요. 현재 '{texts[int(data['respond'])]}'",
                        min_values=1,
                        max_values=1,
                        options=[
                            disnake.SelectOption(label="매너 모드", value="0", description="로이드가 스트라이크를 감지하더라도 알리지 않습니다. 카운트는 추가됩니다.", emoji="🔇"),
                            disnake.SelectOption(label="약하게", value="1", description="로이드가 스트라이크를 감지하면 해당 메시지에 반응을 추가합니다.", emoji="🔉"),
                            disnake.SelectOption(label="적당하게", value="2", description="로이드가 스트라이크를 감지하면 유저를 멘션하며 스트라이크 감지를 알립니다.", emoji="🔊"),
                            disnake.SelectOption(label="시끄럽게", value="3", description="로이드가 스트라이크를 감지하면 스트라이크 감지를 알리고, 해당 메시지를 삭제합니다.", emoji="📣")
                        ],
                        disabled=False,
                        row=0
                    )
                
                async def callback(self, inter: disnake.MessageInteraction) -> None:
                    o = await aiomysql.connect(**inter.bot.config.mysql)
                    c = await o.cursor(aiomysql.DictCursor)
                    await c.execute(f"UPDATE `settings` SET `respond` = '{self.values[0]}' WHERE `guild` = '{inter.guild.id}'")
                    o.close()
                    await inter.response.edit_message(content=f"> {str(self.options[int(self.values[0])].emoji)} 설정 완료! 이제 `{self.options[int(self.values[0])].label}` 상태로 스트라이크에 반응합니다.", view=None)
                    self.view.stop()


            def __init__(self, inter: disnake.ApplicationCommandInteraction, data: dict) -> None:
                super().__init__(timeout=30)
                self.inter = inter
                self.data = data
                self.add_item(self.RespondSelect(data))
            
            async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
                return self.inter.author == inter.author
            
            async def on_timeout(self) -> None:
                await self.inter.delete_original_message()

            @disnake.ui.button(
                label="취소하기",
                style=disnake.ButtonStyle.red,
                emoji="🆖",
                disabled=False,
                row=1
            )
            async def _cancel(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
                await inter.response.pong()
                await self.inter.delete_original_message()
                self.stop()


        def __init__(self, inter: disnake.ApplicationCommandInteraction) -> None:
            super().__init__(timeout=60)
            self.inter = inter
            self.views = {"strict": self.Strict, "respond": self.Respond}
        
        async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
            return inter.author == self.inter.author
        
        async def on_timeout(self) -> None:
            await self.inter.delete_original_message()

        @disnake.ui.string_select(
            placeholder="변경할 설정을 선택해주세요.",
            min_values=1,
            max_values=1,
            options=[
                disnake.SelectOption(label="감지 모드 변경하기", value="strict", description="로이드의 스트라이크 감지 민감도를 설정합니다.", emoji="🚨"),
                disnake.SelectOption(label="응답 유형 변경하기", value="respond", description="로이드가 스트라이크를 감지했을 때의 응답을 조정합니다.", emoji="💬"),
            ],
            disabled=False,
            row=0
        )
        async def _whatToChange(self, select: disnake.ui.StringSelect, inter: disnake.MessageInteraction) -> None:
            o = await aiomysql.connect(**inter.bot.config.mysql)
            c = await o.cursor(aiomysql.DictCursor)
            await c.execute(f"SELECT * FROM `settings` WHERE `guild` = '{inter.guild.id}'")
            rows = await c.fetchall()
            data = rows[0]
            view = self.views[select.values[0]](self.inter, data)
            await inter.response.edit_message(view=view)
            o.close()
            await view.wait()
            self.stop()
        
        @disnake.ui.button(
            label="취소하기",
            style=disnake.ButtonStyle.red,
            emoji="🆖",
            disabled=False,
            row=1
        )
        async def _cancel(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
            await inter.response.pong()
            await self.inter.delete_original_message()
            self.stop()


    class Upload(disnake.ui.Modal):
        def __init__(self, inter: disnake.ApplicationCommandInteraction, strike: str, parent: "Counter") -> None:
            super().__init__(title=f"{strike} 스트라이크에 단어 추가하기", components=[], timeout=3000)
            self.inter = inter
            self.strike = strike
            self.parent = parent
            self.add_text_input(custom_id="words", label="스트라이크 목록", style=disnake.TextInputStyle.paragraph, placeholder="추가할 단어 목록을 입력해주세요. 띄어쓰기로 구분합니다.", required=True, min_length=2, max_length=4000)
        
        async def on_timeout(self) -> None:
            await self.inter.delete_original_message()

        async def callback(self, inter: disnake.ModalInteraction) -> None:
            await inter.response.defer(with_message=True, ephemeral=True)
            o = await aiomysql.connect(**self.parent.bot.config.mysql)
            c = await o.cursor(aiomysql.DictCursor)
            words = inter.text_values["words"].split(" ")
            async for word in self.parent.async_list(words):
                if inter.guild.id not in self.parent.words:
                    self.parent.words[inter.guild.id] = {}
                if self.strike not in self.parent.words[inter.guild.id]:
                    self.parent.words[inter.guild.id][self.strike] = []
                if word not in self.parent.words[inter.guild.id][self.strike]:
                    self.parent.words[inter.guild.id][self.strike].append(word)
                    await c.execute(f"INSERT INTO `detects` VALUES ('{inter.guild.id}', '{word}', '{self.strike}')")
            await inter.edit_original_message(f"> <:popcorn_k:949665093044535336> {self.strike} 스트라이크에 총 {len(words)}개의 단어가 추가되었습니다!\n> ⏳ 변경 사항이 적용되는데 시간이 소요될 수 있습니다.")
            o.close()


    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.settings = {}
        self.words = {}
    
    async def check_admin(self, inter: disnake.ApplicationCommandInteraction) -> bool:
        original = commands.has_permissions(manage_guild=True).predicate
        if inter.guild is None:
            return False
        owner = await inter.bot.is_owner(inter.author)
        if owner is True:
            return True
        else:
            return await original(inter)

    async def find(self, msg: disnake.Message) -> Optional[List[str]]:
        if msg.content.startswith("https://") or msg.content.startswith("http://"):
            return []
        
        mode = self.settings[msg.guild.id]["mode"]

        if mode < 1:
            return []

        result = []

        content = msg.clean_content.lower()
        if mode >= 2:
            exp = re.compile(r"[^a-zA-Zㄱ-ㅎㅏ-ㅣ가-힣]")
            removes = exp.findall(content)
            async for rem in self.async_list(removes):
                content = content.replace(rem, "")
            content.strip()

        async for word in self.async_list(self.words[msg.guild.id]):
            async for detection in self.async_list(self.words[msg.guild.id][word]):
                if mode >= 1:
                    while detection in content:
                        result.append([word, detection])
                        content = content.replace(detection, "", 1)
                if mode == "deprecated":
                    w = re.compile(r"[a-zA-Zㄱ-ㅎㅏ-ㅣ가-힣]".join(detection))
                    finder = w.findall(content)
                    while len(finder) != 0:
                        result.append([word, detection])
                        content = content.replace(detection, "", 1)
                        finder = w.findall(content)

        return result

    async def async_list(self, values: list) -> Any:
        for value in values:
            yield value
            await asyncio.sleep(0)
    
    async def cog_load(self) -> None:
        await self.prepare()
        await self.load_settings()
    
    async def load_settings(self) -> None:
        await self.bot.wait_until_ready()
        self.settings = {}
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute("SELECT * FROM `settings`")
        rows = await c.fetchall()
        async for row in self.async_list(rows):
            self.settings[int(row["guild"])] = {"mode": int(row["mode"]), "respond": int(row["respond"])}

    async def prepare(self) -> None:
        await self.bot.wait_until_ready()
        self.words = {} # {"ssibal": ["ssiba1", "sslbal"]...}
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute("SELECT * FROM `detects`")
        rows = await c.fetchall()
        registered = 0
        category = 0
        guild = 0
        async for row in self.async_list(rows):
            if row["guild"] not in self.words:
                self.words[row["guild"]] = {}
                guild += 1
            if row["word"] not in self.words[row["guild"]]:
                self.words[row["guild"]][row["word"]] = []
                category += 1
            self.words[row["guild"]][row["word"]].append(row["detection"])
            registered += 1
            
        async with aiohttp.ClientSession() as cs:
            webhook = disnake.Webhook.from_url(self.bot.config.webhook, session=cs, bot_token=self.bot.config.token)
            await webhook.send(f"Preparing: {category} categories and total {registered} words in {guild} guilds are registered.", username="로이드 포저", avatar_url=self.bot.user.display_avatar.url)
        o.close()

    @commands.Cog.listener("on_message")
    async def _detectWords(self, msg: disnake.Message) -> None:
        await self.bot.wait_until_ready()
        if msg.author.bot:
            return
        
        if msg.channel.type == disnake.ChannelType.private:
            return
        
        result = await self.find(msg)
        if not result:
            return
        
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        now = time.time()
        async for r in self.async_list(result):
            await c.execute(f"INSERT INTO `counts` VALUES ('{r[0]}', '{r[1]}', '{msg.clean_content}', '{msg.guild.id}', '{msg.author.id}', '{now}')")
        o.close()
        rsp = self.settings[msg.guild.id]["respond"]
        if rsp == 1:
            await msg.add_reaction("<:absolute:1002916291226644572>")
        elif rsp >= 2:
            await msg.channel.send(f"""
> 🌟 {msg.author.mention}님이 스트라이크에 감지되셨습니다!
            """)
            if rsp == 3:
                await msg.delete()
        else:
            pass
    
    @commands.slash_command(name="count", dm_permission=False)
    async def total(self, inter: disnake.ApplicationCommandInteraction) -> None:
        return await inter.response.pong()

    @total.sub_command(name="word", description="특정 트리거에 대한 전체 유저의 사용 수를 조회합니다.")
    async def _totalWord(
        self,
        inter: disnake.ApplicationCommandInteraction,
        word: str = commands.Param(name="스트라이크", desc="조회할 스트라이크를 지정해주세요.")
    ) -> None:
        admin = await self.check_admin(inter)
        if not admin:
            raise commands.NotOwner
        await inter.response.defer()
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"SELECT * FROM `counts` WHERE `word` = '{word}' AND `guild` = '{inter.guild.id}'")
        rows = await c.fetchall()
        if not rows:
            return await inter.edit_original_message(content=f"> <a:clap:949665959084458036> 아직 `{word}` 스트라이크를 발견하지 못했습니다.")
        datas = {}
        async for row in self.async_list(rows):
            if row["user"] not in datas:
                datas[row["user"]] = 1
            else:
                datas[row["user"]] += 1
        content = ">>> ```\n"
        async for d in self.async_list(datas):
            user = inter.guild.get_member(int(d))
            if not user:
                continue
            content += f"{user.display_name} - {datas[d]}회\n"
        content += f"```\n🌟 {inter.guild.name} 서버 내 `{word}` 스트라이크의 감지 횟수는 총 **{len(rows)}회**입니다."
        await inter.edit_original_message(content=content)
        o.close()
    
    @total.sub_command(name="user", description="특정 유저에 대한 전체 스트라이크의 사용 수를 조회합니다.")
    async def _totalUser(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member = commands.Param(name="유저", desc="스트라이크를 조회할 유저를 지정해주세요.")
    ) -> None:
        admin = await self.check_admin(inter)
        if not admin:
            raise commands.NotOwner
        await inter.response.defer()
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"SELECT * FROM `counts` WHERE `user` = '{member.id}' AND `guild` = '{inter.guild.id}'")
        rows = await c.fetchall()
        if not rows:
            return await inter.edit_original_message(content=f"> <a:clap:949665959084458036> **{member.display_name}**님은 아직 스트라이크에 걸리지 않았습니다.")
        datas = {}
        async for row in self.async_list(rows):
            if row["word"] not in datas:
                datas[row["word"]] = 1
            else:
                datas[row["word"]] += 1
        content = ">>> ```\n"
        async for d in self.async_list(datas):
            content += f"{d} - {datas[d]}회\n"
        content += f"```\n🌟 {inter.guild.name} 서버 내 **{member.display_name}**님의 스트라이크 감지 횟수는 총 **{len(rows)}회**입니다."
        await inter.edit_original_message(content=content)
        o.close()

    @commands.slash_command(name="reset", description="서버 내의 스트라이크를 초기화합니다.", dm_permission=False)
    async def _totalReset(self, inter: disnake.ApplicationCommandInteraction) -> None:
        admin = await self.check_admin(inter)
        if not admin:
            raise commands.NotOwner
        await inter.response.send_message(f"""
> 🔄 정말로 **{inter.guild.name}** 서버의 전체 스트라이크 감지를 초기화하시겠습니까?
> **이 작업은 영구적이며, 실행 이후에는 실행 이전으로 되돌릴 수 없습니다!**
> 이를 이해했으며, 초기화 작업을 실행하시겠다면 `{self.bot.user.name}`를 입력하세요.
> 작업 요청은 30초 후에 만료됩니다. 즉시 취소하려면 `취소`를 입력하세요.
        """)
        def check(msg: disnake.Message) -> bool:
            return msg.author == inter.author and msg.channel == inter.channel and msg.content in [msg.guild.me.name, "취소"]
        try:
            msg = await self.bot.wait_for("message", timeout=30, check=check)
        except:
            return await inter.delete_original_message()
        else:
            if msg.content == "취소":
                return await inter.delete_original_message()
            o = await aiomysql.connect(**self.bot.config.mysql)
            c = await o.cursor(aiomysql.DictCursor)
            await c.execute(f"DELETE FROM `counts` WHERE `guild` = '{inter.guild.id}'")
            o.close()
            await inter.delete_original_message()
            await inter.followup.send(content=f"> :wastebasket: **{inter.guild.name}** 서버의 모든 스트라이크 기록을 초기화했습니다.")

    @commands.slash_command(name="settings", description="로이드 포저의 설정을 변경합니다.", dm_permission=False)
    async def _settings(self, inter: disnake.ApplicationCommandInteraction) -> None:
        admin = await self.check_admin(inter)
        if not admin:
            raise commands.NotOwner
        await inter.response.send_message(f"> ⚙️ 현재 {inter.guild.name} 서버의 설정을 변경하고 있습니다...")
        view = self.View(inter)
        await inter.edit_original_message(view=view)
        await view.wait()
        await self.load_settings()

    @commands.slash_command(name="strike", dm_permission=False)
    async def words(self, inter: disnake.ApplicationCommandInteraction) -> None:
        return await inter.response.pong()

    @words.sub_command(name="list", description="현재 서버에 등록되어 있는 모든 스트라이크의 목록을 불러옵니다.")
    async def _wordList(self, inter: disnake.ApplicationCommandInteraction) -> None:
        admin = await self.check_admin(inter)
        if not admin:
            raise commands.NotOwner
        if inter.guild.id not in self.words or not self.words[inter.guild.id]:
            return await inter.response.send_message("> ❌ 현재 서버에 등록된 스트라이크가 없습니다.")
        await inter.response.defer(ephemeral=True)
        content = ""
        async for word in self.async_list(self.words[inter.guild.id]):
            content += f"\n{word} 스트라이크에 추가된 감지어 목록 ({len(self.words[inter.guild.id][word])}개) :\n"
            async for detection in self.async_list(self.words[inter.guild.id][word]):
                content += f"{detection}\n"

        data = io.StringIO(content)
        await inter.edit_original_message(content="> 📜 현재 캐싱된 스트라이크 목록을 보려면 아래 파일을 확인하세요.", file=disnake.File(fp=data, filename="strikes.txt"))

    @words.sub_command(name="add", description="감지할 스트라이크를 추가합니다.")
    async def _addWord(
        self,
        inter: disnake.ApplicationCommandInteraction,
        word: str = commands.Param(name="스트라이크", description="스트라이크의 분류명을 입력하세요."),
    ) -> None:
        admin = await self.check_admin(inter)
        if not admin:
            raise commands.NotOwner
        await inter.response.send_modal(self.Upload(inter, word, self))
    
    @words.sub_command(name="remove", description="추가되어 있는 스트라이크를 삭제합니다.")
    async def _removeWord(
        self,
        inter: disnake.ApplicationCommandInteraction,
        detect: str = commands.Param(name="감지어", description="삭제할 감지어를 입력하세요.")
    ) -> None:
        admin = await self.check_admin(inter)
        if not admin:
            raise commands.NotOwner
        await inter.response.defer(ephemeral=True)
        o = await aiomysql.connect(**self.bot.config.mysql)
        c = await o.cursor(aiomysql.DictCursor)
        await c.execute(f"DELETE FROM `detects` WHERE `detection` = '{detect}' AND `guild` = '{inter.guild.id}'")
        o.close()
        if inter.guild.id not in self.words:
            self.words[inter.guild.id] = {}
            return
        async for word in self.async_list(self.words[inter.guild.id]):
            if detect in self.words[inter.guild.id][word]:
                self.words[inter.guild.id][word].remove(detect)
                if len(self.words[inter.guild.id][word]) == 0:
                    del self.words[inter.guild.id][word]
        await inter.edit_original_message(f"> <:popcorn_k:949665093044535336> {detect} 스트라이크 감지를 삭제했습니다!\n> ⏳ 변경 사항이 적용되는데 시간이 소요될 수 있습니다.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Counter(bot))
