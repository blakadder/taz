from random import randint

import discord
import asyncio
import json
import re

from discord import File
from discord.ext import commands
from discord.utils import get
from datetime import datetime, timedelta

from github import Github
from github.GithubException import UnknownObjectException

from discord_token import TOKEN

with open('links.json') as l:
    links_list = json.load(l)

with open('welcome.txt') as w:
    welcome_mesg = w.read()

with open('remarks.txt') as r:
    remarks = r.read()

muted_users = {}

git = Github()
tasmota = git.get_repo("arendst/Sonoff-Tasmota")

re_issue = re.compile("(?:\A|\s)#(\d{4})")
re_tasmota = re.compile("t[oa][sz]m[ao]t[ao]", re.IGNORECASE)
re_command = re.compile("(?:\s)?\?c (\w*)(?:\b)?")
re_commandq = re.compile("`(\w*)`(?:\b)?")
re_link = re.compile("(?:\s)+\?l (\w*)(?:\b)?")
re_tdm = re.compile("tdm\s+\d+\.\d+", re.IGNORECASE)

options = ["SetOption{}".format(o) for o in range(70)]
comms = options + ["Backlog", "BlinkCount", "BlinkTime", "ButtonDebounce", "FanSpeed", "Interlock", "LedPower", "LedMask", "LedState", "Power", "PowerOnState", "PulseTime", "SwitchDebounce", "SwitchMode", "Delay", "Emulation", "Event", "FriendlyName", "Gpios", "Gpio", "Gpio", "I2Cscan", "LogHost", "LogPort", "Modules", "Module", "OtaUrl", "Pwm", "Pwm", "PwmFrequency", "PwmRange", "Reset", "Restart", "Template", "SaveData", "SerialLog", "Sleep", "State", "Status", "SysLog", "Timezone", "TimeSTD", "TimeDST", "Upgrade", "Upload", "WebLog", "AP", "Hostname", "IPAddress1", "IPAddress2", "IPAddress3", "IPAddress4", "NtpServer", "Password", "Password", "Ssid", "WebPassword", "WebSend", "WebServer", "WifiConfig", "ButtonRetain", "ButtonTopic", "FullTopic", "GroupTopic", "MqttClient", "MqttFingerprint", "MqttHost", "MqttPassword", "MqttPort", "MqttPort", "MqttRetry", "MqttUser", "PowerRetain", "Prefix1", "Prefix2", "Prefix3", "Publish", "Publish2", "SensorRetain", "StateText1", "StateText2", "StateText3", "StateText4", "SwitchRetain", "SwitchTopic", "TelePeriod", "Topic", "Rule", "RuleTimer", "Mem", "Var", "Add", "Sub", "Mult", "Scale", "CalcRes", "Latitude", "Longitude", "Timers", "Timer", "Altitude", "AmpRes", "Counter", "CounterDebounce", "CounterType", "EnergyRes", "HumRes", "PressRes", "Sensor13", "Sensor15", "Sensor27", "Sensor34", "TempRes", "VoltRes", "WattRes", "AmpRes", "CurrentHigh", "CurrentLow", "CurrentSet", "EnergyRes", "EnergyReset", "EnergyReset1", "EnergyReset2", "EnergyReset3", "FreqRes", "FrequencySet", "MaxPower", "MaxPowerHold", "MaxPowerWindow", "PowerDelta", "PowerHigh", "PowerLow", "PowerSet", "Status", "VoltageHigh", "VoltageLow", "VoltageSet", "VoltRes", "WattRes", "Channel", "Color", "Color2", "Color3", "Color4", "Color5", "Color6", "CT", "Dimmer", "Fade", "HsbColor", "HsbColor1", "HsbColor2", "HsbColor3", "Led", "LedTable", "Pixels", "Rotation", "Scheme", "Speed", "Wakeup", "WakeupDuration", "Width1", "Width2", "Width3", "Width4", "Baudrate", "SBaudrate", "SerialDelimiter", "SerialDelimiter", "SerialDelimiter", "SerialSend", "SerialSend2", "SerialSend3", "SerialSend4", "SerialSend5", "SSerialSend", "SSerialSend2", "SSerialSend3", "SSerialSend4", "SSerialSend5", "RfCode", "RfHigh", "RfHost", "RfKey", "RfLow", "RfRaw", "RfSync", "IRsend", "IRhvac", "MP3DAC", "MP3Device", "MP3EQ", "MP3Pause", "MP3Play", "MP3Reset", "MP3Stop", "MP3Track", "MP3Volume", "DomoticzIdx", "DomoticzKeyIdx", "DomoticzSensorIdx", "DomoticzSwitchIdx", "DomoticzUpdateTimer", "KnxTx_Cmnd", "KnxTx_Val", "KNX_ENABLED", "KNX_ENHANCED", "KNX_PA", "KNX_GA", "KNX_GA", "KNX_CB", "KNX_CB", "Display", "DisplayAddress", "DisplayDimmer", "DisplayMode", "DisplayModel", "DisplayRefresh", "DisplaySize", "DisplayRotate", "DisplayText", "DisplayCols", "DisplayRows", "DisplayFont"]

bot = commands.Bot(command_prefix=commands.when_mentioned_or('?'), description="Helper Bot", case_insensitive=True)

@bot.event
async def on_message(message):
    msg = message.content
    found = re.findall(re_issue, msg)
    moto = re.findall(re_tasmota, msg)
    cmnd = re.findall(re_command, msg)
    cmdqt = re.findall(re_commandq, msg)
    lnk = re.findall(re_link, msg)
    tdm = re.findall(re_tdm, msg)
    response = []
    bad = []
    if message.author != bot.user:
        if found:
            for i in found:
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

        # if moto and moto[0].lower() != 'tasmota':
        #     await bot.send_file(message.channel, "tasmoto.png")

        if cmnd or cmdqt:
            result = cmnd + cmdqt

            response = await verify_command(result)
            if response:
                embed = discord.Embed(title="Tasmota Wiki", description="\n".join(response),
                                      colour=discord.Colour(0x3498db))
                await message.channel.send(embed=embed)

        if tdm and message.author.id != 244557530057932800:
            await message.channel.send(content="Your nagging delayed the 0.2 release by another {} days.".format(randint(1, 30)))

        if lnk:
            ctx = await bot.get_context(message)
            await ctx.invoke(link, lnk[0])

    await bot.process_commands(message)


async def verify_command(result):
    response = set(["[{}](<https://github.com/arendst/Sonoff-Tasmota/wiki/Commands#{}>)".format(
        comms[list(map(lambda x: x.lower(), comms)).index(c.lower())], c.lower()) for c in result if
        c.lower() in map(lambda x: x.lower(), comms)])
    return response


@bot.command(aliases=["l", "links"], brief="Return a link or show available links.")
async def link(ctx, lnk: str=''):
    lnk = lnk.lower()
    if lnk and links_list.get(lnk):
        lnk = links_list[lnk]
        embed = discord.Embed(description="[{}](<{}>)".format(lnk[0], lnk[1]),
                              colour=discord.Colour(0x3498db))
    else:
        link_list = " ".join(sorted(
            ["[{}](<{}>): {}\n".format(k, links_list[k][1], links_list[k][0]) for k in links_list.keys()]))
        embed = discord.Embed(title="Available links", description=link_list, colour=discord.Colour(0x3498db))
        embed.set_footer(text="You can click them directly.")
    mentions = [m.mention for m in ctx.message.mentions if not m.bot]
    await ctx.channel.send(embed=embed, content=" ".join(mentions))


@bot.command(aliases=["c", "cmd"], brief="Link to wiki page of command")
async def command(ctx, cmd: str):
    pass


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


@bot.command(aliases=["i"], pass_context=True, brief="Show count of users inactive for <x> days.")
@commands.has_any_role('Admin', 'Moderator')
async def inactive(ctx, days: int=30):
    await ctx.channel.send("{} members are inactive for more than {} day{}.".format(await ctx.message.guild.estimate_pruned_members(days=days), days, "s" if days > 1 else ""))


@bot.command(aliases=["p"], brief="Prune members inactive for <x> days.")
@commands.has_any_role('Admin')
async def prune(ctx, days: int=30):
    await ctx.channel.send("{} members inactive for more than {} day{} were kicked. ".format(await ctx.message.guild.prune_members(days=days), days, "s" if days > 1 else ""))


@bot.command(aliases=["g", "jfgi", "utfg", "foo", "lmg"], brief="Let me Google that for you.")
async def lmgtfy(ctx, *q: str):
    await ctx.channel.send("http://lmgtfy.com/?q={}".format('+'.join(q)))


@bot.command(brief="RTFW")
async def rtfw(ctx):
    await ctx.channel.send(file=File('rtfw.png'))

@bot.command(brief="Re-send welcome message to mentioned user(s)")
async def welcome(ctx):
    for member in ctx.message.mentions:
        await member.send(welcome_mesg)
        await member.send(remarks)


@bot.command(ignore_extras=False, hidden=True)
@commands.has_any_role('Admin')
async def watch(ctx, *args):
    await bot.change_presence(game=discord.Game(name=" ".join(args), type=3))


@bot.event
async def on_member_join(member):
    await member.send(welcome_mesg)
    await member.send(remarks)


@bot.event
async def on_member_update(old, new):
    pass


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


# async def make_reply(message, reply):
#     mentions = " ".join([m.mention for m in message.mentions]) if message.mentions else message.author.mention
#     return "{}\n{}".format(mentions, reply)


# async def command_output(cmd):
#     reply = "Usage: {}\n\n{}".format(cmd['usage'], "\n".join(["**{}**: {}".format(p['name'], p['function']) for p in cmd['params']]))
#     return reply


# async def mentions(message):
#     return " ".join([m.mention for m in message.mentions]) if message.mentions else message.author.mention


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
        await asyncio.sleep(15) # task runs every 60 seconds

if __name__ == "__main__":
    bot.loop.create_task(mute_check())
    bot.run(TOKEN)
