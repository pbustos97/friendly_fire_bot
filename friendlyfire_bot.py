#!/usr/bin/python
import sys
import os
import asyncio
import discord
import numpy as np
from discord.ext import commands
from friendlyfire_bot_id import friendlyfire_bot_token

bot = commands.Bot(command_prefix=commands.when_mentioned_or('$'), description='Friendly Fire Counter Bot')

def loadFile(attacker):
    attackerId = str(attacker.id) + '.npy'
    try:
        dictionary = np.load(attackerId, allow_pickle=True).item()
        print(attackerId + ' file loaded')
    except:
        print('Client ' + attackerId + ' does not have a friendly fire dictionary file yet')
        print('Creating new file for ' + attackerId)
        dictionaryBase = {'NULL':0}
        np.save(attackerId, dictionaryBase)
        dictionary = np.load(attackerId, allow_pickle=True).item()
    return dictionary

# adds friendly fire count to attacker and victim
def friendlyFireMain(message):
    mentions = message.mentions
    author = message.author
    msg = message.content.split()
    if len(msg) == 1:
        return 'Command needs an attacker and victim'
    msg = msg[1:]
    if len(mentions) == 0:
        attacker = author
        dictionary = loadFile(attacker)
        attackerId = str(attacker.id) + '.npy'
        if len(msg) > 1:
            if msg[0].isdigit():
                return friendlyFireCounter(attacker, msg[1], dictionary, attackerId, msg[0])
            elif msg[1].isdigit():
                return friendlyFireCounter(attacker, msg[0], dictionary, attackerId, msg[1])
            else:
                compilation = ''
                for victim in msg:
                    compilation += friendlyFireCounter(attacker, victim, dictionary, attackerId)
                return compilation
        else:
            return friendlyFireCounter(attacker, msg[0], dictionary, attackerId)
    else:
        msg = msg[1:]
        if len(mentions) > 1:
            return 'Only 1 person can be mentioned'
        else:
            attacker = mentions[0]
            dictionary = loadFile(attacker)
            attackerId = str(attacker.id) + '.npy'
            if len(msg) > 1:
                if msg[0].isdigit():
                    return friendlyFireCounter(attacker, msg[1], dictionary, attackerId, msg[0])
                elif msg[1].isdigit():
                    return friendlyFireCounter(attacker, msg[0], dictionary, attackerId, msg[1])
                else:
                    compilation = ''
                    for victim in msg:
                        compilation += friendlyFireCounter(attacker, victim, dictionary, attackerId)
                    return compilation
            else:
                return friendlyFireCounter(attacker, msg[0], dictionary, attackerId)

# adds friendly fire count to attacker and returns string of incidients for victim
def friendlyFireCounter(attacker, victim, victimDictionary, attackerId, count=1):
    count = int(count)
    msg = ''
    if victim in victimDictionary:
        ffCounter = victimDictionary.get(victim)
        ffCounter += count
        victimDictionary[victim] = ffCounter
        msg = '%s attacked %s %s' % (attacker.name, victim, ffCounter)
    elif victim not in victimDictionary:
        victimDictionary[victim] = count
        msg = '%s attacked %s %s' % (attacker.name, victim, count)
    if count == 1:
        msg += ' time\n'
    elif count > 1:
        msg += ' times\n'
    np.save(attackerId, victimDictionary)
    return msg

# returns string of total friendly fire incidents of attacker
def friendlyFireTotal(attacker, victimDictionary):
    totalList = victimDictionary.values()
    totalTk = 0
    for number in totalList:
        totalTk += int(number)
    msg = '%s has attacked teammates a total of %s' % (str(attacker.name), str(totalTk))
    if totalTk == 1:
        msg += ' time'
    elif totalTk > 1:
        msg += ' times'
    return msg

# sends a leaderboard of lowest incidents to highest incidents on discord
def leaderboard():
    msg = '```\n'
    leaderboard = {}
    for file in os.listdir(os.getcwd()):
        if file.endswith(".npy"):
            dictionary = np.load(str(file), allow_pickle=True).item()
            tkList = dictionary.values()
            totalTk = 0
            for number in tkList:
                totalTk += int(number)
            # if userName cannot be found
            try:
                userId = str(file[:-4])
                userId = int(userId)
                user = bot.get_user(userId)
                userName = bot.get_user(userId).name
                leaderboard[userId] = totalTk
            except:
                print('no user error on %s' % (str(userId)))
    counter = 1
    for attacker in sorted(leaderboard.keys(), key=lambda x:leaderboard[x]):
        msg += '%s) %s attacked teammates %s' % (str(counter), bot.get_user(attacker).name, leaderboard[attacker])
        if leaderboard[attacker] == 1:
            msg += ' time\n'
        elif leaderboard[attacker] > 1:
            msg += ' times\n'
        counter += 1
    msg += '\n```'
    return msg

async def dispatch(function, message):
    msg = ''
    func = DISPATCH[function]
    author = message.author
    mentions = message.mentions
    if func == friendlyFireMain:
        msg = func(message)
    if func == friendlyFireTotal:
        msg = func(author, loadFile(author))
    if func == leaderboard:
        msg = func()
    await message.channel.send(msg)

DISPATCH = {
    '!tk'           : friendlyFireMain,
    '!total'        : friendlyFireTotal,
    '!leaderboard'  : leaderboard
}

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return
    msg = message.content.split()
    function = msg[0]
    await dispatch(function, message)


@bot.event
async def on_ready():
    print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))

bot.run(friendlyfire_bot_token)
