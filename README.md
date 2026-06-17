# osuirc

一個 osu! 專用的 IRC 客戶端工具，無第三方套件依賴

目前還在開發中，可能會有巨大的變動

## 安裝

```
pip install -U git+https://github.com/codefz840/osuirc.git
```

## 用法

用法非常簡單，就跟寫 Discord 機器人一樣:

```py
import asyncio
from osuirc import IrcClient
import random
import os

nickname = os.getenv('IRC_NICK')
password = os.getenv('IRC_PASS')

bot = IrcClient(nickname, password, prefix = '?')

# 指令觸發
@bot.command()
async def hello(ctx):
    await ctx.reply(f'Hello {ctx.author}')

# 帶參數的指令
@bot.command()
async def roll(ctx, num=100):
    point = random.randint(0, num)
    await ctx.reply(f'{ctx.author} roll {point} point(s).')

if __name__ == "__main__":
    asyncio.run(bot.run())
```
