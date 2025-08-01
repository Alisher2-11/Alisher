import telebot
from telebot import types
from config import TOKEN, ACCESS_CODE, DB_KLIENT, DB_MEN_KLIENT
from db import *
import pandas as pd

bot = telebot.TeleBot(TOKEN)

user_states = {}
temp_data = {}

def get_db(chat_id):
    return DB_KLIENT if user_states.get(chat_id) == 'admin' else DB_MEN_KLIENT

@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Kirish', 'Info')
    bot.send_message(message.chat.id, "Quyidagilardan birini tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == 'Info')
def info_handler(message):
    bot.send_message(message.chat.id, "Bu bot klientlarni boshqarish uchun mo‘ljallangan. Siz klient qo‘shishingiz, qidirishingiz va ro‘yxatini ko‘rishingiz mumkin.")

@bot.message_handler(func=lambda msg: msg.text == 'Kirish')
def kirish_handler(message):
    msg = bot.send_message(message.chat.id, "Iltimos, kirish kodini kiriting:")
    bot.register_next_step_handler(msg, check_code)

def check_code(message):
    if message.text == ACCESS_CODE:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Mening klientim', 'Men klient')
        bot.send_message(message.chat.id, "Muvaffaqiyatli!", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Kod noto‘g‘ri. Qayta urinib ko‘ring.")
        start_handler(message)

@bot.message_handler(func=lambda msg: msg.text == 'Mening klientim')
def admin_menu(message):
    user_states[message.chat.id] = 'admin'
    init_db(DB_KLIENT)
    show_client_menu(message)

@bot.message_handler(func=lambda msg: msg.text == 'Men klient')
def user_menu(message):
    user_states[message.chat.id] = 'user'
    init_db(DB_MEN_KLIENT)
    show_client_menu(message)

def show_client_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Klient qo‘shish')
    markup.add('Klientni qidirish')
    markup.add('Klientlar ro‘yxati')
    bot.send_message(message.chat.id, "Menyudan birini tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == 'Klient qo‘shish')
def add_client_start(message):
    temp_data[message.chat.id] = {}
    msg = bot.send_message(message.chat.id, "Ismini kiriting:")
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    temp_data[message.chat.id]['name'] = message.text
    msg = bot.send_message(message.chat.id, "Telefon raqamini kiriting:")
    bot.register_next_step_handler(msg, get_phone)

def get_phone(message):
    temp_data[message.chat.id]['phone'] = message.text
    msg = bot.send_message(message.chat.id, "Joylashuvini kiriting:")
    bot.register_next_step_handler(msg, get_location)

def get_location(message):
    temp_data[message.chat.id]['location'] = message.text
    msg = bot.send_message(message.chat.id, "Qo‘shimcha ma’lumot kiriting:")
    bot.register_next_step_handler(msg, get_info)

def get_info(message):
    temp_data[message.chat.id]['info'] = message.text
    data = temp_data[message.chat.id]
    text = f"Ismi: {data['name']}\nTelefon: {data['phone']}\nJoylashuv: {data['location']}\nMa’lumot: {data['info']}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Save", callback_data='save_client'))
    markup.add(types.InlineKeyboardButton("Delete", callback_data='cancel_client'))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'save_client')
def save_client(call):
    data = temp_data.get(call.message.chat.id)
    if data:
        db = get_db(call.message.chat.id)
        add_client(db, data['name'], data['phone'], data['location'], data['info'])
        bot.edit_message_text("✅ Saqlandi!", call.message.chat.id, call.message.message_id)
        temp_data.pop(call.message.chat.id, None)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_client')
def cancel_client(call):
    bot.edit_message_text("❌ Bekor qilindi.", call.message.chat.id, call.message.message_id)
    temp_data.pop(call.message.chat.id, None)

@bot.message_handler(func=lambda msg: msg.text == 'Klientni qidirish')
def search_client(message):
    msg = bot.send_message(message.chat.id, "Telefon raqamini kiriting:")
    bot.register_next_step_handler(msg, do_search)

def do_search(message):
    phone = message.text
    db = get_db(message.chat.id)
    client = get_client_by_phone(db, phone)
    if client:
        text = f"Ismi: {client[1]}\nTelefon: {client[2]}\nJoylashuv: {client[3]}\nMa’lumot: {client[4]}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Tahrirlash", callback_data=f'edit_{client[2]}'))
        markup.add(types.InlineKeyboardButton("O‘chirish", callback_data=f'delete_{client[2]}'))
        bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Bunday klient topilmadi.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_callback(call):
    phone = call.data.split('_')[1]
    delete_client(get_db(call.message.chat.id), phone)
    bot.edit_message_text("🗑 O‘chirildi.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_'))
def edit_callback(call):
    phone = call.data.split('_')[1]
    temp_data[call.message.chat.id] = {'edit_phone': phone}

    new_text = "Qaysi qatorni tahrirlaysiz?"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Ismni tahrirlash", callback_data='edit_name'))
    markup.add(types.InlineKeyboardButton("Telefonni tahrirlash", callback_data='edit_phone'))
    markup.add(types.InlineKeyboardButton("Joylashuvni tahrirlash", callback_data='edit_location'))
    markup.add(types.InlineKeyboardButton("Ma’lumotni tahrirlash", callback_data='edit_info'))
    markup.add(types.InlineKeyboardButton("Orqaga", callback_data='cancel_edit'))

    try:
        bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        if "message is not modified" not in str(e):
            raise e

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_'))
def edit_field_handler(call):
    field = call.data.replace('edit_', '')
    msg = bot.send_message(call.message.chat.id, f"Yangi {field} ni kiriting:")
    bot.register_next_step_handler(msg, process_edit_field, field)

def process_edit_field(message, field):
    new_value = message.text
    phone = temp_data[message.chat.id]['edit_phone']
    update_client_field(get_db(message.chat.id), phone, field, new_value)
    bot.send_message(message.chat.id, "✅ Yangilandi.")
    temp_data.pop(message.chat.id, None)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_edit')
def cancel_edit(call):
    bot.edit_message_text("Bekor qilindi.", call.message.chat.id, call.message.message_id)
    temp_data.pop(call.message.chat.id, None)

@bot.message_handler(func=lambda msg: msg.text == 'Klientlar ro‘yxati')
def export_clients(message):
    db = get_db(message.chat.id)
    data = get_all_clients(db)
    if not data:
        bot.send_message(message.chat.id, "Hech qanday klient topilmadi.")
        return

    df = pd.DataFrame(data, columns=['ID', 'Ismi', 'Telefon', 'Joylashuv', 'Ma’lumot'])
    file_name = f"clients_{message.chat.id}.xlsx"
    df.to_excel(file_name, index=False)

    with open(file_name, 'rb') as f:
        bot.send_document(message.chat.id, f)

if __name__ == '__main__':
    bot.polling(none_stop=True)


    
