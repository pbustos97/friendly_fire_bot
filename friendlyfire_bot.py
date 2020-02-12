#!/usr/bin/python
import sys
import os
import string
import collections
import operator
import asyncio
import discord
import numpy as np
from discord.ext import commands
from friendlyfire_bot_id import friendlyfire_bot_token

# changed description
bot = commands.Bot(command_prefix=commands.when_mentioned_or('$'), description='User Command Bot')

# adds friendly fire count to attacker
async def tk(attacker, target, ffDict, clientId, message, channel):
    msg = ''
    if target in ffDict:
        ffCounter = ffDict.get(target)
        ffCounter += 1
        ffDict[target] = ffCounter
        msg = attacker + ' attacked ' + target + ' ' + str(ffCounter) + ' times'
    elif target not in ffDict:
        ffDict[target] = 1
        msg = attacker + ' attacked ' + target + ' 1 time'
    np.save(clientId, ffDict)
    await channel.send(msg)
    

# gets total friendly fire incidents of attacker
async def _total(attacker, ffDict, message, channel):
    totalList = ffDict.values()
    totalTk = 0
    for number in totalList:
        totalTk += int(number)
    msg = str(attacker.name) + ' has attacked teammates a total of ' + str(totalTk) + ' times'
    await channel.send(msg)

@bot.event
async def on_message(message):
    if message.author != bot.user:
        clientId = str(message.author.id) + '.npy'
        channel = message.channel

        # Does not work if np.load(clientId).item() doesn't exist
        try:
            ffDict = np.load(clientId, allow_pickle=True).item()
            print(clientId + ' file loaded')
        except:
            print('Client ' + clientId + ' does not have friendly fire dictionary file yet')
            print('Creating new file for ' + clientId)
            ffDictBase = {'test':0}
            np.save(clientId, ffDictBase)
            ffDict = np.load(clientId).item()

        msg = message.content.split()

        # add tk counts to self
        if msg[0] == '!tk':
            if len(msg) > 1:
                msg = msg[1:]
                for target in msg:
                    await tk(message.author.name, str(target), ffDict, clientId, message, channel)
            else:
                await channel.send('Who did you attack?')


        # add tk counts to other players
        # Mention = attacker, text = victim / total
        elif msg[0] == '!ff':
            if len(message.mentions) == 1:
                attacker = message.mentions[0]
                attackerId = str(attacker.id) + '.npy'
                victimList = msg[2:]
                try:
                    ffDict = np.load(attackerId, allow_pickle=True).item()
                    print(attackerId + ' file loaded')
                except:
                    print('Client ' + attackerId + ' does not have friendly fire dictionary file yet')
                    print('Creating new file for ' + attackerId)
                    ffDictBase = {'test':0}
                    np.save(attackerId, ffDictBase)
                    ffDict = np.load(attackerId).item()
                if victimList[0] == 'total':
                    await _total(attacker, ffDict, message, channel)
                elif victimList[0] != 'total':
                    for victim in victimList:
                        await tk(str(attacker.name), str(victim), ffDict, attackerId, message, channel)
            else:
                await channel.send('Only 1 person can be mentioned')

        # adds total times of tk for message sender
        elif msg[0] == '!total':
            await _total(message.author, ffDict, message, channel)

        # ranks by lowest amount of tk per server
        elif msg[0] == '!leaderboard' or msg[0] == '!lb':
            msg = '```\n'
            leaderboard = {}
            for file in os.listdir(os.getcwd()):
                if file.endswith(".npy"):
                    ffDict = np.load(str(file)).item()
                    totalList = ffDict.values()
                    totalTk = 0
                    for number in totalList:
                        totalTk += int(number)
                    try:
                        userId = str(file[:-4])
                        userId = int(userId)
                        user = bot.get_user(userId)
                        userName = bot.get_user(userId).name
                        leaderboard[userId] = totalTk
                    except:
                        print('no user error on ' + str(userId))
            counter = 1
            for attacker in sorted(leaderboard.keys(), key=lambda x:leaderboard[x]):
                msg += str(counter) + ') ' + '%s attacked teammates %s times \n' % (bot.get_user(attacker).name, leaderboard[attacker])
                counter += 1
            msg += '\n```'
            await channel.send(msg)

@bot.event
async def on_ready():
    print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))

bot.run(friendlyfire_bot_token)