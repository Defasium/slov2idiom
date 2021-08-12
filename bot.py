#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import os
import telebot
from telebot import types
from search import search_idiom
from flask import Flask, request

TOKEN = os.environ.get('TG_TOKEN', '')
APP_URL = os.path.join(os.environ.get('APP_URL', ''), TOKEN)
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, ''.join(['Hello, ', message.from_user.first_name]))


@bot.message_handler(func=lambda _: True, content_types=['text'])
def echo(message):
    #results = search_idiom(message.text)
    #print(message.text, results)
    bot.reply_to(message, message.text)
    #bot.reply_to(message, '\n'.join([str(i+1)+'. '+' | '.join(res) for res in enumerate(results)]))


'''CLICKED_BY = []

#Handler for command: '/btn_test'
@bot.message_handler(commands=['btn_test'])
def command_1(msg):
    cid = msg.chat.id
    mid = msg.message_id
    uid = msg.from_user.id

    if msg.chat.type != "private":
        click_kb = types.InlineKeyboardMarkup()
        click_button = types.InlineKeyboardButton("CLICK HERE", callback_data='clicked')
        click_kb.row(click_button)
        bot.send_message(cid, "<b>Hey friend...</b>", parse_mode="HTML", reply_markup=click_kb, disable_web_page_preview=True)
    else:
        bot.send_message(cid, "Use me in groups, please.", reply_to_message_id=mid)

@bot.callback_query_handler(func=lambda call: call.data == 'clicked')
def command_click_inline(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    mid = call.message.message_id

    if uid not in CLICKED_BY:
        CLICKED_BY.append(uid)
        click_kb_edited = types.InlineKeyboardMarkup()
        click_edited = types.InlineKeyboardButton("CLICK HERE ({} clicks)".format(len(CLICKED_BY)), callback_data='clicked')
        click_kb_edited.row(click_edited)
        bot.edit_message_text("<b>Hey friend...</b>", cid, mid, reply_markup=click_kb_edited, parse_mode="HTML")
        bot.answer_callback_query(call.id, text="Thanks for click me {}.".format(call.from_user.first_name))
    else:
        bot.answer_callback_query(call.id, text="You already clicked this button!")'''


@server.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200


@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    return '!', 200


if __name__=='__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))