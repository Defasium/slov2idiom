#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Telegram bot for slov2idiom search via webhook.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

"""
import os
import telebot
from telebot import types
from search import search_idiom, find_nn_by_hash, construct_table, construct_idiom_info, \
                   make_one_hash, make_random_hash
from flask import Flask, request

TOKEN = os.environ.get('TG_TOKEN', '')
APP_URL = os.path.join(os.environ.get('APP_URL', ''), TOKEN)
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
HISTORY = {}


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, ''.join(['👋, ', message.from_user.first_name]))


@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message,
                 'Введи запрос и я найду тебе похожие по смыслу идиомы.\n'
                 '[*Больше информации тут*](github.com/Defasium/slov2idiom)',
                 parse_mode='Markdown')


def update_history(args):
    mdhash = make_one_hash(args[0])
    HISTORY[mdhash] = args
    return 'H|'+mdhash


def construct_keyboard(results, idx, undo=None):
    keyboard = types.InlineKeyboardMarkup()
    if undo is not None:
        callback_data = update_history(undo)
        get_back_btn = types.InlineKeyboardButton(text='◀ назад'.upper(), callback_data=callback_data)
        keyboard.add(get_back_btn)
    for i, res in zip(idx, results):
        keyboard.add(types.InlineKeyboardButton(text=res[0].upper(), callback_data=str(i)))
    keyboard.add(generate_random_btn())
    return keyboard


def generate_random_btn():
    return types.InlineKeyboardButton(text='🎲 случайная идиома'.upper(),
                                      callback_data=make_random_hash())
        

@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def recommend(message):
    try:
        results, idx = search_idiom(message.text, return_index=True)
        HISTORY[str(message.chat.id)] = results, idx
        bot.reply_to(message, construct_table(results), parse_mode='Markdown',
                     reply_markup=construct_keyboard([('🔎 поиск по идиомам',)], ['search']))
    except Exception as e:
        print(e)
        bot.reply_to(message, 'Ошибка')


@bot.inline_handler(func=lambda query: len(query.query) > 4)
def query_text(query):
    results = search_idiom(query.query)
    answers = []
    for i, res in enumerate(results):
        answers.append(types.InlineQueryResultArticle(id=str(i+1), title=res[0].upper(),
                                               description=res[1].lower(),
                                               input_message_content=types.InputTextMessageContent(
                                               message_text=res[0].lower())))
    bot.answer_inline_query(query.id, answers, cache_time=2147483646) # 68 years


@bot.callback_query_handler(func=lambda call: call.message)
def callback_message(call):
    if call.data.startswith('H|'):
        mdhash = call.data[2:]
        if mdhash in HISTORY:
            restored_data = HISTORY[mdhash]
            reply_markup = types.InlineKeyboardMarkup.de_json(restored_data[0])
            print(reply_markup)
            reply_markup.keyboard[0] = reply_markup.keyboard[0][:-1]
            reply_markup.add(generate_random_btn())
            text = restored_data[-1]
        else:
            reply_markup = None
            text = call.message.text
            bot.send_message(chat_id=call.message.chat.id, text='Ошибка! Время истекло')
    else:
        mdhash = call.data
        restored_data = HISTORY.get(str(call.message.chat.id), None)
        if (mdhash == 'search') and (restored_data is not None):
            results, idx = restored_data
            text = '*Поиск похожих идиом*🔎'
        else:
            results, idx = find_nn_by_hash(mdhash, return_index=True)
            text = construct_idiom_info(results[0])
            results, idx = results[1:], idx[1:]
        undo = (call.message.reply_markup.to_json(), call.message.text)
        reply_markup = construct_keyboard(results, idx, undo=undo)
    try:
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=text, reply_markup=reply_markup,
                              parse_mode='Markdown')
    except Exception as e:
        print(e)


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