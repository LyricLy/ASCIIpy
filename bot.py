import ascii
import aiohttp
import discord
import functools
import subprocess
import io
import string

from discord.ext import commands
from typing import Optional
from PIL import Image


bot = commands.Bot(command_prefix="@")


@bot.event
async def on_ready():
    bot.session = aiohttp.ClientSession()
    print(f"Ready on {bot.user}")
    print(f"ID: {bot.user.id}")
    print("---")

@bot.command()
@commands.is_owner()
async def update(ctx):
    subprocess.call(["git", "pull"])
    await ctx.bot.close()
    await bot.session.close()

@bot.command(name="ascii")
async def _ascii(
    ctx,
    dither: Optional[bool] = True,
    invert: Optional[bool] = False,
    url=None, font="Consolas",
    *, charset=string.ascii_letters + string.punctuation + string.digits + " "
):
    font = ascii.get_font(font)
    if url:
        async with bot.session.get(url) as resp:
            image = Image.open(io.BytesIO(await resp.read()))
    elif ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        image = Image.open(io.BytesIO(await attachment.read()))
    else:
        return await ctx.send("You forgot the image.")

    out_image = io.BytesIO()
    result = await bot.loop.run_in_executor(None, functools.partial(
         ascii.full_convert,
         image,
         invert=invert,
         font=font,
         spacing=0,
         charset=charset,
         out_text=False,
         dither=dither
    ))
    result.save(out_image, format="png")
    out_image.seek(0)
    await ctx.send(file=discord.File(out_image, "result.png"))


with open("token.txt") as f:
    bot.run(f.read()[:-1])
