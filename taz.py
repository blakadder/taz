import discord
import json

from discord_token import TOKEN

with open('commands.json') as c:
    cmds = json.load(c)

with open('links.json') as l:
    links = json.load(l)

client = discord.Client()

help_mesg = """I provide quick access to various commands used in Tasmota software.
If you know the exact command (without parameters), use prefix "!" to read its summary (for example `!switchtopic`).
Alternatively, you can use prefix "?" so I can find commands by partial name (for example `?topic`)."""

welcome_mesg = """Hello and welcome to the Tasmota Discord server!

If you have generic questions regarding settings, functionality, or need help with configuration of your device, feel free to ask in the #general channel.
Do you think you've encountered a bug? The device doesn't work as expected? The #issues channel is for such questions.
This is not strictly enforced, however please do not post the same issue in both channels.

Solutions or suggestions related to common issues and problems, especially for those new to Tasmota and compatible devices, are available on our wiki:

https://github.com/arendst/Sonoff-Tasmota/wiki/Initial-Configuration
https://github.com/arendst/Sonoff-Tasmota/wiki/FAQs
https://github.com/arendst/Sonoff-Tasmota/wiki/Troubleshooting (especially this one)

Please keep in mind that we're all volunteers here. Please be polite and patient. While we allow off-topic conversations, the channels are moderated. Flooding the chat, spamming links, being rude etc. is a quick way to be kicked (and/or banned, depending on the case).

Just be a decent human being and we'll all get along just fine."""

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content == "!help":
        await client.send_message(message.author, help_mesg)

    elif message.content == "!test":
        # embed = discord.Embed(title="LedState", colour=discord.Colour(0x3afabd), description="Usage: `ledstate <parameter>` where _parameter_ is one of:")
        #
        # embed.add_field(name="_None_", value="Show current led state as 0 to 7", inline=False)
        # embed.add_field(name="0 / off", value="Disable use of LED as much as possible", inline=False)
        # embed.add_field(name="1 / on", value="Disable use of LED as much as possible", inline=False)
        # embed.add_field(name="2", value="Show MQTT subscriptions as a led blink", inline=False)
        # embed.add_field(name="3", value="Show power state and MQTT subscriptions as a led blink", inline=False)
        # embed.add_field(name="4", value="Show MQTT publications as a led blink", inline=False)
        # embed.add_field(name="5", value="Show power state and MQTT publications as a led blink", inline=False)
        # embed.add_field(name="6", value="Show all MQTT messages as a led blink", inline=False)
        # embed.add_field(name="7", value="Show power state and MQTT messages as a led blink", inline=False)

        desc = """Usage: `ledstate <parameter>` where _parameter_ is one of:
        
        **_None_**: Show current led state as 0 to 7
        **0 / off**: Disable use of LED as much as possible
        **1 / on**: Disable use of LED as much as possible
        """

        embed = discord.Embed(title="LedState", colour=discord.Colour(0x3afabd),
                              description=desc)

        await client.send_message(message.channel, embed=embed)

    elif message.content.startswith('!') and len(message.content) > 1:
        cmd = cmds.get(message.content.split(" ")[0][1:].lower(), None)

        if cmd:
            reply = await make_reply(message, "\n".join(cmd))
        else:
            reply = await make_reply(message, "Unknown command. Use ! prefix for Tasmota commands, ? prefix to search and + for shortlinks.")

        await client.send_message(message.channel, reply)

    elif message.content.startswith("+links"):
        link_list = ["+{}".format(k) for k in links.keys()]
        reply = await make_reply(message, "Available links:\n{}".format(" ".join(link_list)))
        await client.send_message(message.channel, reply)

    elif message.content.startswith('+') and len(message.content) > 1:
        lnk = links.get(message.content.split(" ")[0][1:].lower(), None)

        if lnk:
            reply = await make_reply(message, lnk)

        else:
            reply = await make_reply(message, "Shortlink not found. +links to see the list.")

        await client.send_message(message.channel, reply)

    elif message.content.startswith('?') and len(message.content) > 1:
        cmd = message.content.split(" ")[0][1:].lower()
        result = [c for c in cmds.keys() if cmd in c]

        if result:
            if len(result) > 10:

                reply = await make_reply(message, "Search yielded too many results. Narrow your query.")
            else:
                reply = await make_reply(message, "I've found these commands:\n```{}```".format(" ".join(result)))

        else:
            reply = await make_reply(message, "No commands found")

        await client.send_message(message.channel, reply)


@client.event
async def on_member_join(member):
    await client.send_message(member, welcome_mesg)


@client.event
async def on_ready():
    print('Logged in as {} ({})'.format(client.user.name, client.user.id))

async def make_reply(message, reply):
    mentions = " ".join([m.mention for m in message.mentions]) if message.mentions else message.author.mention
    return "{}\n{}".format(reply, mentions)

client.run(TOKEN)
