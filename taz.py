import discord
import asyncio
import json
import re

from discord.ext import commands
from discord.utils import get
from datetime import datetime, timedelta

from github import Github
from github.GithubException import UnknownObjectException

from discord_token import TOKEN

with open('commands.json') as c:
    cmds = json.load(c)

with open('commands2.json') as c2:
    cmds2 = json.load(c2)

with open('options.json') as o:
    opts = json.load(o)

with open('links.json') as l:
    links_list = json.load(l)

with open('welcome.txt') as w:
    welcome_mesg = w.read()

with open('remarks.txt') as r:
    remarks = r.read()

with open('help.txt') as h:
    help_mesg = h.read()

muted_users = {}

git = Github()
tasmota = git.get_repo("arendst/Sonoff-Tasmota")

re_issue = re.compile("(?:\A|\s)#(\d{1,5})")
re_tasmota = re.compile("[Tt]a[sz]moto")

bot = commands.Bot(command_prefix=['?'], description="Helper Bot", case_insensitive=False)

@bot.event
async def on_message(message):
    msg = message.content
    found = re.findall(re_issue, msg)
    moto = re.findall(re_tasmota, msg)
    response = []
    bad = []
    if found:
        for i in found:
            try:
                issue = tasmota.get_issue(number=int(i))
                response.append("[#{}: {}](<https://github.com/arendst/Sonoff-Tasmota/issues/{}>)".format(i, issue.title, i))
            except Exception as error:
                if isinstance(error, UnknownObjectException):
                    bad.append(i)
        if bad:
            response.append("{} not found.".format(", ".join([i for i in sorted(bad)])))
        embed = discord.Embed(title="Tasmota issues", description="\n".join(response), colour=discord.Colour(0x3498db))
        await bot.send_message(message.channel, embed=embed)

    if moto:
        await bot.send_file(message.channel, "tasmoto.png")

    await bot.process_commands(message)

@bot.command(aliases=["l", "links"], pass_context=True, brief="Return a link or show available links.")
async def link(ctx, link: str=''):
    if link and links_list.get(link):
        link = links_list[link]
        await bot.send_message(ctx.message.channel, "<{}>".format(link))
    else:
        link_list = " ".join(sorted(["[{}](<{}>)".format(k, links_list[k]) for k in links_list.keys()]))
        embed = discord.Embed(title="Available links", description=link_list, colour=discord.Colour(0x3498db))
        embed.set_footer(text="You can click them directly.")
        await bot.say(embed=embed)


@bot.command(aliases=["o", "setoption", "so"], pass_context=True, brief="Show SetOption description and usage.")
async def option(ctx, nr: str):
    if opts.get(nr) and opts[nr]['enabled']:
        option = opts[nr]
        embed = discord.Embed(title="SetOption"+nr, description=option['desc'], colour=discord.Colour(0x3498db))
        embed.add_field(name="Usage", value="SetOption{} {}".format(nr, option['params']), inline=False)
        embed.set_footer(text="Every SetOption used without parameters returns current setting.")

    else:
        embed = discord.Embed(description="SetOption{} not found.".format(nr), colour=discord.Colour(0x3498db))
    await bot.say(embed=embed)


@bot.command(aliases=["c", "cmd"], pass_context=True, brief="Link to wiki page of command")
async def command(ctx, cmd: str):
    await bot.say("<https://github.com/arendst/Sonoff-Tasmota/wiki/Commands#{}>".format(cmd))


@bot.command(aliases=["m"], pass_context=True, brief="Mute a user or show the list of currently muted users.")
@commands.has_any_role('Admin', 'Moderator')
async def mute(ctx, member: discord.Member=None, duration: int=5):
    if member and member == bot.user:
        embed = discord.Embed(
            title="Yeah, good luck with that", colour=discord.Colour(0x3498db), description="I'd laugh if I had a sense of humor.")
        await bot.say(content=member.mention, embed=embed)
    elif member:
        muted_users[member] = datetime.now() + timedelta(minutes=duration)
        await bot.add_roles(member, get(member.server.roles, name="Muted"))
        embed = discord.Embed(title="{} has been muted in all channels for {} minute{}".format(member.name, duration, "s" if duration > 1 else ""), colour=discord.Colour(0x3498db),
                              description="Consider this a warning.")
        await bot.say(content=member.mention, embed=embed)
    else:
        embed = discord.Embed(title="Currently muted members", colour=discord.Colour(0x3498db))
        for member, duration in muted_users.items():
            embed.add_field(name=member.name, value=duration.strftime("Until %Y-%m-%d %H:%M"), inline=False)
        await bot.say(embed=embed)


@bot.command(aliases=["u"], pass_context=True, brief="Unmute a user.")
@commands.has_any_role('Admin', 'Moderator')
async def unmute(ctx, member: discord.Member):
    if muted_users.get(member, None):
        await bot.remove_roles(member, get(member.server.roles, name="Muted"))
        embed = discord.Embed(title="{} is no longer muted".format(member.name), colour=discord.Colour(0x2ecc71))
    else:
        embed = discord.Embed(title="{} is not currently muted".format(member.name), colour=discord.Colour(0x3498db))
    await bot.say(embed=embed)


@bot.command(aliases=["i"], pass_context=True, brief="Show count of users inactive for <x> days.")
@commands.has_any_role('Admin', 'Moderator')
async def inactive(ctx, days: int=30):
    await bot.say("{} members are inactive for more than {} day{}.".format(await bot.estimate_pruned_members(server=ctx.message.server, days=days), days, "s" if days > 1 else ""))


@bot.command(aliases=["p"], pass_context=True, brief="Prune members inactive for <x> days.")
@commands.has_any_role('Admin')
async def prune(ctx, days: int=30):
    await bot.say("{} members inactive for more than {} day{} were kicked. ".format(await bot.prune_members(server=ctx.message.server, days=days), days, "s" if days > 1 else ""))


@bot.command(pass_context=True, ignore_extras=False, hidden=True)
@commands.has_any_role('Admin')
async def watch(ctx, *args):
    await bot.change_presence(game=discord.Game(name=" ".join(args), type=3))


@bot.event
async def on_member_join(member):
    await bot.send_message(member, welcome_mesg)
    await bot.send_message(member, remarks)


@bot.event
async def on_command_error(error, ctx):
    embed = discord.Embed(title="Command error", colour=discord.Colour(0xe74c3c))
    if isinstance(error, commands.MissingRequiredArgument):
        embed.description = "Required argument is missing."
    await bot.send_message(ctx.message.channel, embed=embed)


@bot.event
async def on_ready():
    print('Logged in as {} ({})'.format(bot.user.name, bot.user.id))


async def make_reply(message, reply):
    mentions = " ".join([m.mention for m in message.mentions]) if message.mentions else message.author.mention
    return "{}\n{}".format(mentions, reply)


async def command_output(cmd):
    reply = "Usage: {}\n\n{}".format(cmd['usage'], "\n".join(["**{}**: {}".format(p['name'], p['function']) for p in cmd['params']]))
    return reply


async def mentions(message):
    return " ".join([m.mention for m in message.mentions]) if message.mentions else message.author.mention


async def mute_check():
    await bot.wait_until_ready()
    while not bot.is_closed:
        for member, d in list(muted_users.items()):
            if datetime.now() >= muted_users[member]:
                await bot.remove_roles(member, get(member.server.roles, name="Muted"))
                embed = discord.Embed(title="You are no longer muted", colour=discord.Colour(0x2ecc71))
                await bot.send_message(member, content=member.mention, embed=embed)
                del muted_users[member]
                print("Unmuted {}".format(member.name))
                asyncio.sleep(1)
        await asyncio.sleep(15) # task runs every 60 seconds

if __name__ == "__main__":
    bot.loop.create_task(mute_check())
    bot.run(TOKEN)
