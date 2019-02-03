import discord
import asyncio
from discord.ext import commands
from discord.utils import get
from datetime import datetime, timedelta
import json
import re

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

with open('help.txt') as h:
    help_mesg = h.read()

muted_users = {}

re_issue = re.compile("#(\d{1,5})")

bot = commands.Bot(command_prefix=['?'], description="Helper Bot", case_insensitive=False)

@bot.event
async def on_message(message):
    msg = message.content
    found = re.findall(re_issue, msg)
    if found:
        issues = ["[{}](<https://github.com/arendst/Sonoff-Tasmota/issues/{}>)".format(i,i) for i in found]
        embed = discord.Embed(title="GitHub issues mentioned", description=", ".join(issues), colour=discord.Colour(0x3498db))
        await bot.send_message(message.channel, embed=embed)

    await bot.process_commands(message)

#     elif message.content == "!test":
#         cmd = cmds2['power']
#
#         embed = discord.Embed(title=cmd['name'], colour=discord.Colour(0x3afabd), description=await command_output(cmd),
#                               url="https://github.com/arendst/Sonoff-Tasmota/wiki/Commands#{}".format(cmd['group']))
##
#         if cmd['options']:
#             embed.description += "\n\nSetOptions related to this command:\n"
#
#             for o in cmd['options']:
#                 embed.description += "\n`setoption{}` {}".format(o, opts["setoption{}".format(o)]['params'][0]['function'])
#                 #embed.add_field(name="setoption{}".format(o), value=opts["setoption{}".format(o)]['params'][0]['function'], inline=False)
#
#         embed.set_footer(text="Click the function name to see other commands from group {}".format(cmd['group']))
#
#         await client.send_message(message.channel, embed=embed)
#
#     elif message.content.startswith('!') and len(message.content) > 1:
#         cmd = cmds.get(message.content.split(" ")[0][1:].lower(), None)
#
#         if cmd:
#             reply = await make_reply(message, "\n".join(cmd))
#         else:
#             reply = await make_reply(message, "Unknown command. Use ! prefix for Tasmota commands, ? prefix to search and + for shortlinks.")
#
#         await client.send_message(message.channel, reply)
#

#
#     elif message.content.startswith('?') and len(message.content) > 1:
#         cmd = message.content.split(" ")[0][1:].lower()
#         result = [c for c in cmds.keys() if cmd in c]
#         print(result)
#
#         if result:
#             if len(result) > 15:
#                 reply = await make_reply(message, "Search yielded too many results. Narrow your query.")
#             else:
#                 reply = await make_reply(message, "I've found these commands:\n```{}```".format(" ".join(result)))
#
#         else:
#             reply = await make_reply(message, "No commands found")
#
#         await client.send_message(message.channel, reply)

@bot.command(pass_context=True, brief="Return a link or show available links.")
async def l(ctx, link: str=''):
    if link and links_list.get(link):
        link = links_list[link]
        await bot.send_message(ctx.message.channel, "<{}>".format(link))
    else:
        link_list = " ".join(sorted(["[{}](<{}>)".format(k, links_list[k]) for k in links_list.keys()]))
        embed = discord.Embed(title="Available links", description=link_list, colour=discord.Colour(0x3498db))
        embed.set_footer(text="You can click them directly.")
        await bot.say(embed=embed)


@bot.command(pass_context=True, brief="Show SetOption description and usage.")
async def o(ctx, nr: str):
    if opts.get(nr) and opts[nr]['enabled']:
        option = opts[nr]
        embed = discord.Embed(title="SetOption"+nr, description=option['desc'], colour=discord.Colour(0x3498db))
        embed.add_field(name="Usage", value="SetOption{} {}".format(nr, option['params']), inline=False)
        embed.set_footer(text="Every SetOption used without parameters returns current setting.")

    else:
        embed = discord.Embed(description="SetOption{} not found.".format(nr), colour=discord.Colour(0x3498db))
    await bot.say(embed=embed)


@bot.command(pass_context=True, brief="Mute a user or show the list of currently muted users.")
@commands.has_any_role('Admin', 'Moderator')
async def m(ctx, member: discord.Member=None, duration: int=5):
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


@bot.command(pass_context=True, brief="Unmute a user.")
@commands.has_any_role('Admin', 'Moderator')
async def u(ctx, member: discord.Member):
    if muted_users.get(member, None):
        await bot.remove_roles(member, get(member.server.roles, name="Muted"))
        embed = discord.Embed(title="{} is no longer muted".format(member.name), colour=discord.Colour(0x2ecc71))
    else:
        embed = discord.Embed(title="{} is not currently muted".format(member.name), colour=discord.Colour(0x3498db))
    await bot.say(embed=embed)


# @bot.command(pass_context=True)
# async def issue(ctx, issue: int):
#     if ctx.prefix in ['+']:
#         await bot.say("https://github.com/arendst/Sonoff-Tasmota/issues/{}".format(issue))


@bot.command(pass_context=True, brief="Show count of users inactive for <x> days.")
@commands.has_any_role('Admin', 'Moderator')
async def i(ctx, days: int=30):
    await bot.say("{} members are inactive for more than {} day{}.".format(await bot.estimate_pruned_members(server=ctx.message.server, days=days), days, "s" if days > 1 else ""))


@bot.command(pass_context=True, brief="Prune members inactive for <x> days.")
@commands.has_any_role('Admin')
async def p(ctx, days: int=30):
    await bot.say("{} members inactive for more than {} day{} were kicked. ".format(await bot.prune_members(server=ctx.message.server, days=days), days, "s" if days > 1 else ""))


@bot.command(pass_context=True, ignore_extras=False, hidden=True)
@commands.has_any_role('Admin')
async def watch(ctx, *args):
    await bot.change_presence(game=discord.Game(name=" ".join(args), type=3))


@bot.event
async def on_member_join(member):
    await bot.send_message(member, welcome_mesg)


@bot.event
async def on_command_error(error, ctx):
    embed = discord.Embed(title="Command error", colour=discord.Colour(0xe74c3c))
    if isinstance(error, commands.MissingRequiredArgument):
        embed.description = "Required argument is missing."
    await bot.send_message(ctx.message.channel, embed=embed)



@bot.event
async def on_ready():
    # await bot.change_presence(game=discord.Game(name="photos of post girls", type = 3))
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

bot.loop.create_task(mute_check())
bot.run(TOKEN)
