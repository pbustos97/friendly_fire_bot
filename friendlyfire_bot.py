#!/usr/bin/python
import sys
import os
import asyncio
import discord
import numpy as np
import sqlite3 as sql
from discord.ext import commands
from friendlyfire_bot_id import friendlyfire_bot_token

bot = commands.Bot(command_prefix=commands.when_mentioned_or('$'), description='Friendly Fire Counter Bot')

# Adds friendly fire count to attacker and victim
def friendlyFireMain(message, conn, c):
    mentions = message.mentions
    if len(mentions) > 1 or len(mentions) < 1:
        return '!tk only accepts a single mention'
    msg = ''
    attacker = mentions[0]
    victims = message.content.split()
    if len(victims) == 2:
        return '!tk needs victims'
    victimList = victims[2:]

    # Used if user wants to add multiple incidents at the same time for a single victim
    if len(victimList) == 2:
        if victimList[1].isdigit():
            return friendlyFireHelper(attacker, victimList, 0, 1, conn, c)
        elif victimList[0].isdigit():
            return friendlyFireHelper(attacker, victimList, 1, 0, conn, c)

    for victim in victimList:
        with conn:
            c.execute("INSERT INTO friendlyfire VALUES(:discordId, :victim, datetime('now', 'localtime'))", {'discordId':attacker.id, 'victim':victim})
            c.execute("SELECT discordId, victim, COUNT(victim) FROM friendlyFire WHERE discordId = :discordId AND victim = :victim", {'discordId':attacker.id, 'victim':victim})
        temp = c.fetchone()
        count = temp[2]
        name = bot.get_user(attacker.id).name
        msg += '%s has attacked %s %s ' % (name, victim, count)
        if count == 1:
            msg += 'time\n'
        else:
            msg += 'times\n'
    return msg

# For the isdigit section of friendlyFireMain
def friendlyFireHelper(attacker, victimList, x, y, conn, c):
    count = 0
    msg = ''
    victim = victimList[x]
    while count != int(victimList[y]):
        with conn:
            c.execute("INSERT INTO friendlyfire VALUES(:discordId, :victim, datetime('now', 'localtime'))", {'discordId':attacker.id, 'victim':victim})
        count += 1
    c.execute("SELECT discordId, victim, COUNT(victim) FROM friendlyFire WHERE discordId = :discordId AND victim = :victim", {'discordId':attacker.id, 'victim':victim})
    temp = c.fetchone()
    name = bot.get_user(attacker.id)
    count = temp[2]
    msg += '%s has attacked %s %s ' % (name, victim, count)
    if count == 1:
        msg += 'time\n'
    else:
        msg += 'times\n'
    return msg

# Returns string of total friendly fire incidents of attacker with most recent incident displayed first
def friendlyFireTotal(message, conn, c):
    mentions = message.mentions
    if len(mentions) > 1 or len(mentions) < 1:
        return '!total only accepts a single mention'
    attacker = mentions[0]
    msg = '```\n'
    c.execute("SELECT discordId, victim, COUNT(victim), MAX(date) FROM friendlyFire WHERE discordId = :discordId GROUP BY victim ORDER BY date DESC", {'discordId':attacker.id})
    ffList = c.fetchall()
    name = bot.get_user(int(attacker.id)).name
    if not ffList:
        return '%s has not attacked anyone yet' % (name)
    for incident in ffList:
        victim = incident[1]
        incidents = incident[2]
        date = incident[3]
        msg += '%s attacked %s %s ' % (name, victim, str(incidents))
        if incidents == 1:
            msg += 'time as recently as %s Los Angeles Time\n\n' % (date)
        else:
            msg += 'times as recently as %s Los Angeles Time\n\n' % (date)
    msg += '```'
    return msg

# Sends a leaderboard of highest incidents first
def leaderboard(conn, c):
    c.execute("SELECT discordId, COUNT(victim) FROM friendlyFire GROUP BY discordId ORDER BY COUNT(victim) DESC")
    leaderboard = c.fetchall()
    if not leaderboard:
        return 'Nobody has been attacked yet on this server'
    msg = '```\n'
    counter = 0
    for attacker in leaderboard:
        counter += 1
        name = bot.get_user(int(attacker[0])).name
        incidents = str(attacker[1])
        msg += '%s) %s has attacked teammates a total of %s ' % (str(counter), name, incidents)
        if attacker[1] == 1:
            msg += 'time\n'
        else:
            msg += 'times\n'
    msg += '```'
    return msg

def assist():
    msg = '```\n'
    msg += '!tk @attacker victim1 victim2 victim3 ...\n'
    msg += '!forgive @attacker victim1 victim2 victim3 ...\n'
    msg += '!total @attacker\n'
    msg += '!leaderboard\n'
    msg += '!dead @victim game number (Do not include mention to report own death)\n'
    msg += '!deadLeaderboard\n'
    msg += '```'
    return msg

# Removes an incident by most recent date for a victim
def forgive(message, conn, c):
    mentions = message.mentions
    if len(mentions) > 1 or len(mentions) < 1:
        return '!forgive only accepts a single mention'
    attacker = mentions[0]
    msg = message.content.split()
    victims = msg[2:]
    for victim in victims:
        with conn:
            c.execute("DELETE FROM friendlyFire WHERE discordId = :discordId and victim = :victim and date = (SELECT MAX(date) FROM friendlyFire WHERE victim = :victim AND discordId = :discordId)", {'discordId':attacker.id, 'victim':victim})
    return friendlyFireTotal(message, conn, c)

def newDeath(message, conn, cursor):
    mentions = message.mentions
    msg = ''
    game = ''
    if len(mentions) > 1:
        msg = '!dead only accepts a single mention or no mention'
    victim = message.author
    victimId = victim.id
    message = message.content.split()
    # Add death to mentioned user
    if len(mentions) == 1 and len(message) > 2:
        victim = mentions[0]
        victimId = victim.id
        game = ' '.join(message[2:])
        deadCount = message[-1]
        if deadCount.isdigit():
            game = ' '.join(message[2:-1])
            for i in range(0, int(deadCount)):
                cursor.execute("INSERT INTO deathTable VALUES(:discordId, :game, datetime('now', 'localtime'))", {'discordId':victimId, 'game':game})
        else:
            cursor.execute("INSERT INTO deathTable VALUES(:discordId, :game, datetime('now', 'localtime'))", {'discordId':victimId, 'game':game})

    # Add death to author
    elif len(mentions) == 0 and len(message) > 1:
        game = ' '.join(message[1:])
        deadCount = message[-1]
        if deadCount.isdigit():
            game = ' '.join(message[1:-1])
            for i in range(0, int(deadCount)):
                cursor.execute("INSERT INTO deathTable VALUES(:discordId, :game, datetime('now', 'localtime'))", {'discordId':victimId, 'game':game})
        else:
            cursor.execute("INSERT INTO deathTable VALUES(:discordId, :game, datetime('now', 'localtime'))", {'discordId':victimId, 'game':game})

    else:
        return '!dead needs a game, an optional count, and/or an optional mention'

    cursor.execute("SELECT discordId, count(game) FROM deathTable WHERE game = :game AND discordId = :discordId GROUP BY discordId", {'game':game, 'discordId':victimId})
    temp = cursor.fetchone()
    deathCount = temp[1]
    msg = '%s has died %d times in %s' % (bot.get_user(victimId).name, deathCount, game)
    return msg

def deadLeaderboard(message, conn, cursor):
    msg = ''
    cursor.execute("SELECT discordId, count(game) FROM deathTable GROUP BY discordId ORDER BY COUNT(game) DESC")
    leaderboard = cursor.fetchall()
    if not leaderboard:
        return 'Nobody has had a significant death in the server yet'
    msg = '```\n'
    counter = 0
    for person in leaderboard:
        counter += 1
        name = bot.get_user(int(person[0])).name
        deaths = str(person[1])
        msg += '%s) %s has died a total of %s times\n' % (str(counter), name, deaths)

    msg += '```'
    return msg


async def dispatch(function, message, conn, cursor):
    msg = ''
    func = DISPATCH[function]
    author = message.author
    mentions = message.mentions
    if func == friendlyFireMain:
        msg = func(message, conn, cursor)
    if func == friendlyFireTotal:
        msg = func(message, conn, cursor)
    if func == leaderboard:
        msg = func(conn, cursor)
    if func == forgive:
        msg = func(message, conn, cursor)
    if func == deadLeaderboard:
        msg = func(message, conn, cursor)
    if func == newDeath:
        msg = func(message, conn, cursor)
    if func == assist:
        msg = func()
    await message.channel.send(msg)

DISPATCH = {
    '!tk'               : friendlyFireMain,
    '!total'            : friendlyFireTotal,
    '!leaderboard'      : leaderboard,
    '!forgive'          : forgive,
    '!dead'             : newDeath,
    '!deadleaderboard'  : deadLeaderboard,
    '!help'             : assist,
}

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    serverId = message.guild.id
    database = str(serverId) + '.db'

    conn = sql.connect(database)
    c = conn.cursor()

    try:
        c.execute("""CREATE TABLE friendlyFire (
                    discordId INTEGER,
                    victim TEXT,
                    date TEXT
                    )""")
        print('friendlyFire table created')
    except sql.Error as error:
        print('Error with table creation: ', error)
    try:
        c.execute("""CREATE TABLE deathTable (
                    discordId INTEGER,
                    game TEXT,
                    date TEXT
                    )""")
        print('deathTable table created')
    except sql.Error as error:
        print('Error with table creation: ', error)

    msg = message.content.split()
    function = msg[0].lower()
    await dispatch(function, message, conn, c)

    conn.commit()
    conn.close()


@bot.event
async def on_ready():
    print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))

bot.run(friendlyfire_bot_token)
