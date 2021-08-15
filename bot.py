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
from search import search_idiom, construct_table, construct_idiom_info, make_one_hash, find_nn_by_hash
from flask import Flask, request

TOKEN = os.environ.get('TG_TOKEN', '')
APP_URL = os.path.join(os.environ.get('APP_URL', ''), TOKEN)
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
HISTORY = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, ''.join(['Hello, ', message.from_user.first_name]))


@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, 'Type your query and I will find idioms')

'''
@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def recommend(message):
    try:
        results = search_idiom(message.text)
        bot.reply_to(message, construct_table(results), parse_mode='Markdown')
        return
    except Exception as e:
        print(e)
    bot.reply_to(message, 'Error')
'''
def update_history(keyboard):
    mdhash = make_one_hash(keyboard)
    HISTORY[mdhash] = keyboard
    return 'H|'+mdhash


def construct_keyboard(resutls, idx, undo=None):
    keyboard = types.InlineKeyboardMarkup()
    if undo is not None:
        keyboard.add(types.InlineKeyboardButton(text="◀ Назад", callback_data=update_history(undo.to_json())))
    for i, res in zip(idx, results):
        keyboard.add(types.InlineKeyboardButton(text=res[0].upper(), callback_data=str(i)))
    return keyboard
        

@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def recommend(message):
    try:
        results, idx = search_idiom(message.text, return_index=True)
        bot.reply_to(message, construct_table(results), parse_mode='Markdown',
                     reply_markup=construct_keyboard(resutls, idx))
        return
    except Exception as e:
        print(e)
    bot.reply_to(message, 'Error')


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
    print(call.data)
    if call.data == "test":
        try:
            print(call.message.reply_markup)
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  reply_markup=call.message.reply_markup,
                                  message_id=call.message.message_id, text="Пыщь")
        except Exception as e:
            print(e)
    if call.data.startswith('H|'):
        mdhash = call.data[2:]
        try:
            if mdhash in HISTORY:       
                keyboard = types.InlineKeyboardMarkup.de_json(HISTORY[mdhash])
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      reply_markup=keyboard,
                                      message_id=call.message.message_id,
                                      text="Результаты поиска по запросу")
            else:
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text=call.message.text)
                bot.send_message(chat_id=call.message.chat.id, text='Ошибка! Время истекло')
        except Exception as e:
            print(e)
    else:
        mdhash = call.data
        results, idx = find_nn_by_hash(mdhash, return_index=True)
        keyboard = construct_keyboard(results, idx, undo=call.message.reply_markup)
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=construct_idiom_info(results[0]),
                              parse_mode='Markdown', reply_markup=keyboard)


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