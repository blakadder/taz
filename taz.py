import discord
import asyncio
import json
import re

from datetime import datetime

from discord import File
from discord.ext import commands
from discord.utils import get
from datetime import datetime, timedelta

from github import Github
from github.GithubException import UnknownObjectException

from discord_token import TOKEN

with open('links.json') as l:
    links_dict = json.load(l)

with open('commands.json') as c:
    commands_dict = json.load(c)

with open('welcome.txt') as w:
    welcome_mesg = w.read()

with open('remarks.txt') as r:
    remarks = r.read()

muted_users = {}

git = Github()
tasmota = git.get_repo("arendst/Sonoff-Tasmota")

re_issue = re.compile("(?:\A|\s)#(\d{4})")
re_command = re.compile("(?:\s)?\?c (\w*)(?:\b)?|`(\w*)`(?:\b)?", re.IGNORECASE)
re_link = re.compile("(?:\s)?\?l (\w*)(?:\b)?|\[(\w*)\](?:\b)?")

bot = commands.Bot(command_prefix=commands.when_mentioned_or('?'), description="Helper Bot", case_insensitive=True)


@bot.event
async def on_message(message):
    msg = message.content
    issues = re.findall(re_issue, msg)
    cmnd = re.findall(re_command, msg)
    lnks = re.findall(re_link, msg)
    response = []
    bad = []

    if message.author != bot.user:
        ctx = await bot.get_context(message)
        if issues:
            for i in issues:
                try:
                    nr = int(i)
                    if nr >= 1000:
                        issue = tasmota.get_issue(number=nr)
                        response.append("[#{}: {}](<https://github.com/arendst/Sonoff-Tasmota/issues/{}>)".format(i, issue.title, i))
                except Exception as error:
                    if isinstance(error, UnknownObjectException):
                        bad.append(i)
            if bad:
                response.append("{} not found.".format(", ".join([i for i in sorted(bad)])))
            embed = discord.Embed(title="Tasmota issues", description="\n".join(response), colour=discord.Colour(0x3498db))
            await message.channel.send(embed=embed)

        if cmnd:
            parsed_cmnds = set(sorted([c for result in cmnd for c in result if c]))
            await ctx.invoke(command, parsed_cmnds)

        if lnks:
            parsed_links = set(sorted([l for result in lnks for l in result if l]))
            await ctx.invoke(links, parsed_links)

    await bot.process_commands(message)


# COMMANDS #
@bot.command(aliases=["l"], brief="Return a link or show available links.")
async def links(ctx, keywords: str=''):
    print(keywords)
    if not isinstance(keywords, str):
        found_links = []
        for keyword in keywords:
            keyword = keyword.lower()
            if links_dict.get(keyword):
                lnk = links_dict[keyword]
                found_links.append("[{}](<{}>)".format(lnk["description"], lnk["url"]))
                embed = discord.Embed(description="\n".join(found_links), colour=discord.Colour(0x3498db))

    elif not keywords:
        link_list = " ".join(sorted(
            ["[{}](<{}>): {}\n".format(k, links_dict[k]["url"], links_dict[k]["description"]) for k in links_dict.keys()]))
        embed = discord.Embed(title="Available links", description=link_list, colour=discord.Colour(0x3498db))
        embed.set_footer(text="You can click them directly.")

    mentions = [m.mention for m in ctx.message.mentions if not m.bot]
    await ctx.channel.send(embed=embed, content=" ".join(mentions))


@commands.has_any_role('Admin', 'Moderator', "Contributor")
@bot.group(name="link", aliases=["ls"])
async def link_group(ctx):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(title="Error", colour=discord.Colour(0xe74c3c), description="Invalid command passed")
        await ctx.send(embed=embed)


@link_group.command(name="add", brief="Add a link")
async def link_add(ctx, keyword: str, url: str, *description: str):
    keyword = keyword.lower()
    description = " ".join(description)

    if await find_link(keyword, url):
        embed = discord.Embed(title="Error", colour=discord.Colour(0xe74c3c), description="This keyword or this url is already present")
        await ctx.send(embed=embed)

    else:
        links_dict[keyword] = {"description": description, "url": url}
        with open('links.json', "w") as l:
            json.dump(links_dict, l, indent=2)

        with open('links.log', "a+") as log:
            log.write("{} {} added link '{}: {} ({})'\n".format(datetime.strftime(datetime.now(), "%x %X"), ctx.message.author, keyword, description, url))

        embed = discord.Embed(title="Success", description="Added link '{}'".format(keyword), colour=discord.Colour(0x7ED321))
        await ctx.channel.send(embed=embed)


@link_group.command(name="del", brief="Delete a link")
async def link_del(ctx, keyword: str):
    keyword = keyword.lower()
    lnk = await find_link(keyword)
    print(lnk)
    if lnk:
        links_dict.pop(lnk)
        with open('links.json', "w") as l:
            json.dump(links_dict, l, indent=2)

        with open('links.log', "a+") as log:
            log.write(
                "{} {} deleted link '{}'\n".format(datetime.strftime(datetime.now(), "%x %X"), ctx.message.author, keyword))

        embed = discord.Embed(title="Success", description="Deleted link '{}'".format(lnk), colour=discord.Colour(0x7ED321))
        await ctx.channel.send(embed=embed)
    else:
        embed = discord.Embed(title="Error", colour=discord.Colour(0xe74c3c), description="Link '{}' not found".format(keyword))
        await ctx.send(embed=embed)

# COMMANDS #
@bot.command(aliases=["c", "cmd"], brief="Link to wiki page of command")
async def command(ctx, cmds):
    if not isinstance(cmds, str):
        found_commands = []
        for cmd in cmds:
            cmnd = await find_command(cmd)
            if cmnd:
                found_commands.append("[{}](<https://github.com/arendst/Sonoff-Tasmota/wiki/Commands#{}>)".format(cmnd, cmnd))

        if found_commands:
            embed = discord.Embed(title="Tasmota Commands Wiki", description="\n".join(found_commands),
                                  colour=discord.Colour(0x3498db))
            await ctx.channel.send(embed=embed)


@commands.has_any_role('Admin', 'Moderator', "Contributor")
@bot.group(name="commands", aliases=["cs"])
async def command_group(ctx):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(title="Error", colour=discord.Colour(0xe74c3c), description="Invalid command passed")
        await ctx.send(embed=embed)


@command_group.command(name="add", brief="Add a Tasmota command")
async def command_add(ctx, cmd: str):
    cmnd = await find_command(cmd)
    if cmnd:
        embed = discord.Embed(title="Error", colour=discord.Colour(0xe74c3c), description="Command already exists")
        await ctx.send(embed=embed)
    else:
        commands_dict.update({cmd: {}})
        with open('commands.json', "w") as c:
            json.dump(commands_dict, c, indent=2)

        with open('command.log', "a+") as log:
            log.write("{} {} added command '{}'\n".format(datetime.strftime(datetime.now(), "%x %X"), ctx.message.author, cmd))

        embed = discord.Embed(title="Success", description="Added command '{}'".format(cmd), colour=discord.Colour(0x7ED321))
        await ctx.channel.send(embed=embed)


@command_group.command(name="del", brief="Delete a Tasmota command")
async def command_del(ctx, cmd: str):
    cmnd = await find_command(cmd)
    if cmnd:
        commands_dict.pop(cmnd)
        with open('commands.json', "w") as c:
            json.dump(commands_dict, c, indent=2)

        with open('command.log', "a+") as log:
            log.write("{} {} deleted command '{}'\n".format(datetime.strftime(datetime.now(), "%x %X"), ctx.message.author, cmd))

        embed = discord.Embed(title="Success", description="Deleted command '{}'".format(cmd), colour=discord.Colour(0x7ED321))
        await ctx.channel.send(embed=embed)
    else:
        embed = discord.Embed(title="Error", colour=discord.Colour(0xe74c3c), description="Command '{}' not found".format(cmd))
        await ctx.send(embed=embed)

# MUTE/UNMUTE #
@bot.command(aliases=["m"], brief="Mute a user or show the list of currently muted users.")
@commands.has_any_role('Admin', 'Moderator')
async def mute(ctx, member: discord.Member=None, duration: int=5):
    if member and member == bot.user:
        embed = discord.Embed(
            title="Yeah, good luck with that", colour=discord.Colour(0x3498db), description="I'd laugh if I had a sense of humor.")
        await ctx.channel.send(content=member.mention, embed=embed)
    elif member:
        muted_users[member] = datetime.now() + timedelta(minutes=duration)
        await bot.add_roles(member, get(member.server.roles, name="Muted"))
        embed = discord.Embed(title="{} has been muted in all channels for {} minute{}".format(member.name, duration, "s" if duration > 1 else ""), colour=discord.Colour(0x3498db),
                              description="Consider this a warning.")
        await ctx.channel.send(content=member.mention, embed=embed)
    else:
        embed = discord.Embed(title="Currently muted members", colour=discord.Colour(0x3498db))
        for member, duration in muted_users.items():
            embed.add_field(name=member.name, value=duration.strftime("Until %Y-%m-%d %H:%M"), inline=False)
        await ctx.channel.send(embed=embed)


@bot.command(aliases=["u"], pass_context=True, brief="Unmute a user.")
@commands.has_any_role('Admin', 'Moderator')
async def unmute(ctx, member: discord.Member):
    if muted_users.get(member, None):
        await bot.remove_roles(member, get(member.server.roles, name="Muted"))
        embed = discord.Embed(title="{} is no longer muted".format(member.name), colour=discord.Colour(0x2ecc71))
    else:
        embed = discord.Embed(title="{} is not currently muted".format(member.name), colour=discord.Colour(0x3498db))
    await ctx.channel.send(embed=embed)

# PRUNING #
@bot.command(aliases=["i"], pass_context=True, brief="Show count of users inactive for <x> days.")
@commands.has_any_role('Admin', 'Moderator')
async def inactive(ctx, days: int=30):
    await ctx.channel.send("{} members are inactive for more than {} day{}.".format(await ctx.message.guild.estimate_pruned_members(days=days), days, "s" if days > 1 else ""))


@bot.command(aliases=["p"], brief="Prune members inactive for <x> days.")
@commands.has_any_role('Admin')
async def prune(ctx, days: int=30):
    await ctx.channel.send("{} members inactive for more than {} day{} were kicked. ".format(await ctx.message.guild.prune_members(days=days), days, "s" if days > 1 else ""))

# HELPERS #
@bot.command(aliases=["g", "jfgi", "utfg", "foo", "lmg"], brief="Let me Google that for you.")
async def lmgtfy(ctx, *q: str):
    await ctx.channel.send("http://lmgtfy.com/?q={}".format('+'.join(q)))


@bot.command(aliases=["rtfm"], brief="RTFW")
async def rtfw(ctx):
    await ctx.channel.send(file=File('rtfw.png'))

# WELCOME #
@bot.command(brief="Re-send welcome message to mentioned user(s)")
async def welcome(ctx):
    if ctx.message.mentions:
        for member in ctx.message.mentions:
            if not member.bot:
                await member.send(welcome_mesg)
                await member.send(remarks)
    else:
        await ctx.message.author.send(welcome_mesg)
        await ctx.message.author.send(remarks)
    await ctx.channel.send("Welcome message sent.")

# EVENTS #
@bot.event
async def on_member_join(member):
    await member.send(welcome_mesg)
    await member.send(remarks)


@bot.event
async def on_command_error(ctx, error):
    embed = discord.Embed(title="Command error", colour=discord.Colour(0xe74c3c))
    if isinstance(error, commands.MissingRequiredArgument):
        embed.description = "Required argument is missing."
    elif isinstance(error, commands.CommandNotFound):
        embed.description = "Command unknown."
    else:
        embed.description = str(type(error)) + "\n" + str(error.original)
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    print('Logged in as {} ({})'.format(bot.user.name, bot.user.id))


async def find_command(cmd):
    for cmnd in commands_dict.keys():
        if cmd == cmnd.lower():
            return cmnd


async def find_link(keyword, url=""):
    for k, v in links_dict.items():
        if k == keyword:
            return k
        elif v["url"].lower() == url.lower():
            return k


async def mute_check():
    await bot.wait_until_ready()
    while not bot.is_closed:
        for member, d in list(muted_users.items()):
            if datetime.now() >= muted_users[member]:
                await bot.remove_roles(member, get(member.server.roles, name="Muted"))
                embed = discord.Embed(title="You are no longer muted", colour=discord.Colour(0x2ecc71))
                await member.send(content=member.mention, embed=embed)
                del muted_users[member]
                print("Unmuted {}".format(member.name))
                asyncio.sleep(1)
        await asyncio.sleep(15)

if __name__ == "__main__":
    bot.loop.create_task(mute_check())
    bot.run(TOKEN)
