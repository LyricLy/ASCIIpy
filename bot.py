import ascii
import aiohttp
import discord
import functools
import subprocess
import traceback
import io
import os
import string
import sys

from discord.ext import commands
from typing import Optional
from PIL import Image


if not os.getcwd().endswith("ASCIIpy"):
    os.chdir(os.path.dirname(__file__))

bot = commands.Bot(command_prefix="@")


@bot.event
async def on_ready():
    bot.session = aiohttp.ClientSession()
    print(f"Ready on {bot.user}")
    print(f"ID: {bot.user.id}")
    print("---")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send("You messed up writing the command.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        if hasattr(error, "original"):
            error = error.original
        await ctx.send(discord.utils.escape_mentions(
             f"Something went wrong. ``{type(error).__name__}: {discord.utils.escape_markdown(str(error))}``"
        ))
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

@bot.command()
@commands.is_owner()
async def update(ctx):
    subprocess.call(["git", "pull"])
    await ctx.bot.close()
    await bot.session.close()

@bot.command()
async def owner(ctx):
    await ctx.send("LyricLy made this bot. Shower him with praise!")

@bot.group(name="ascii", invoke_without_command=True)
async def _ascii(
    ctx,
    in_scale: Optional[float] = 1, out_scale: Optional[float] = 1,
    dither: Optional[bool] = True,
    invert: Optional[bool] = False,
    out_text: Optional[bool] = False,
    url=None, font="Consolas",
    *, charset=string.ascii_letters + string.punctuation + string.digits + " "
):
    font = ascii.get_font(font)
    if not font:
        await ctx.send("Invalid font.")
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        data = await attachment.read()
        filename = attachment.filename
    elif url:
        async with bot.session.get(url) as resp:
            data = await resp.read()
        filename = url.split("?", 1)[0].rsplit("/", 1)[1]
    else:
        return await ctx.send("You forgot the image.")

    image = Image.open(io.BytesIO(data))

    await ctx.send("Performing conversion...")
    result = await bot.loop.run_in_executor(None, functools.partial(
         ascii.full_convert,
         image,
         invert=invert,
         font=font,
         spacing=0,
         charset=charset,
         out_text=out_text,
         dither=dither,
         in_scale=in_scale,
         out_scale=out_scale
    ))

    if out_text:
        await ctx.send(file=discord.File(io.BytesIO(result.encode()), filename + ".txt"))
    else:
        out_image = io.BytesIO()
        result.save(out_image, format="png")
        out_image.seek(0)
        if not filename.endswith(".png"):
            filename = "output.png"
        await ctx.send(file=discord.File(out_image, filename))

@_ascii.group()
async def fonts(ctx):
    out = subprocess.check_output(["fc-list", ":mono"]).decode()
    font = set()
    for ln in out.splitlines():
        font.add(ln.split(":")[1].strip())
    await ctx.send(embed=discord.Embed(description="\n".join(font)))


with open("token.txt") as f:
    bot.run(f.read()[:-1])
