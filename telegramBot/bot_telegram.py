from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


import re
from decimal import Decimal

from db_postgre import Database
from config_db import host, password, user, db_name

db_post = Database(host, password, user, db_name)

bot = Bot(token='5638546081:AAFE8IS-Ssv-fIrb4pdf8UXOqMgngz5trXo')
dp = Dispatcher(bot)

inkb = InlineKeyboardMarkup(row_width=1)

profile_btn = InlineKeyboardButton(text="Профиль", callback_data='show_profile')
add_balance_btn = InlineKeyboardButton(text="Пополнение баланса", callback_data='add_balance')
transfer_btn = InlineKeyboardButton(text="Перевод", callback_data='transfer')
change_nickname_btn = InlineKeyboardButton(text="Изменение Никнейма", callback_data='change_nickname')
history_btn = InlineKeyboardButton(text="История переводов", callback_data='show_history')


inkb.add(profile_btn, add_balance_btn, transfer_btn, change_nickname_btn, history_btn)


@dp.message_handler(commands=['commands'])
async def show_functions(message: types.Message):
    await message.answer('Cписок команд', reply_markup=inkb)


@dp.callback_query_handler(text='show_profile')
async def show_profile(callback: types.CallbackQuery):
    db_post.set_action(callback.from_user.id, 'done')
    await bot.send_message(callback.from_user.id, db_post.show_info(callback.from_user.id))
    await callback.answer()


@dp.callback_query_handler(text='show_history')
async def show_history(callback: types.CallbackQuery):
    db_post.set_action(callback.from_user.id, 'done')

    for i in db_post.get_transaction_info(callback.from_user.id):
        await bot.send_message(callback.from_user.id, f'Кому: {i[0]}\nСумма: {i[1]}\nВремя: {i[2]}\n______________')
    await callback.answer()


@dp.callback_query_handler(text='add_balance')
async def add_balance(callback: types.CallbackQuery):
    db_post.set_action(callback.from_user.id, 'setbalance')
    await bot.send_message(callback.from_user.id, 'Введите сумму')
    await callback.answer()


@dp.callback_query_handler(text='transfer')
async def transfer(callback: types.CallbackQuery):
    db_post.set_action(callback.from_user.id, 'transfer_1')
    await bot.send_message(callback.from_user.id, 'Введите номер телефона адресата')
    await callback.answer()


@dp.callback_query_handler(text='change_nickname')
async def change_nickname(callback: types.CallbackQuery):
    db_post.set_action(callback.from_user.id, 'setnickname')
    await bot.send_message(callback.from_user.id, 'Введите никнейм')
    await callback.answer()


@dp.message_handler(commands=['start', 'help'])
async def commands_start(message: types.Message):
    if (not db_post.user_exists(message.from_user.id)):
        db_post.add_user(message.from_user.id, message.from_user.first_name)
        await message.answer('Введите ваш номер телефона')
    else:
        await bot.send_message(message.from_user.id, 'Вы уже зарегистрированы!\nДля просмотра команд введите /commands')


@dp.message_handler()
async def bot_message(message: types.Message):
    if message.chat.type == 'private':
        if db_post.get_action(message.from_user.id) == 'set_phone':
            valid_check = "^\\+?[1-9][0-9]{7,14}$"
            if re.match(valid_check, message.text) is not None:
                if len(message.text) == 11 or ('+' in message.text and len(message.text) == 12):
                    db_post.set_phone(message.from_user.id, message.text)
                    db_post.set_action(message.from_user.id, 'done')
                    await bot.send_message(message.from_user.id, 'Вы уже закончили регистрацию!\nДля просмотра команд введите /commands')
                else:
                    await bot.send_message(message.from_user.id, 'Вы ввели недопустимое количество цифр')
            else:
                await bot.send_message(message.from_user.id, 'Введите номер без пробелов и дефисов')
        elif db_post.get_action(message.from_user.id) == 'setbalance':
            try:
                if float(message.text) < 0:
                    await bot.send_message(message.from_user.id, 'Вы не можете вводить отрицательные числа')
                elif float(message.text) < 500:
                    await bot.send_message(message.from_user.id, 'Минимальная сумма для пополнения составляет 500')
                elif float(message.text) > 5000000:
                    await bot.send_message(message.from_user.id, 'Максимальная сумма для пополнения составляет 5,000,000')
                elif Decimal(str(float(message.text))).as_tuple().exponent * (-1) > 2:
                    await bot.send_message(message.from_user.id, 'Вы можете ввести только 2 числа после запятой')
                else:
                    db_post.set_balance(message.from_user.id, float(message.text))
                    db_post.set_action(message.from_user.id, 'done')
                    await bot.send_message(message.from_user.id, f'Ваш баланс теперь составляет: {round(db_post.get_balance(message.from_user.id),2)}')
            except Exception:
                await bot.send_message(message.from_user.id, 'Введите число корректно')
        elif db_post.get_action(message.from_user.id) == 'setnickname':
            if len(message.text) <= 11:
                db_post.set_nickname(message.from_user.id, message.text)
                db_post.set_action(message.from_user.id, 'done')
                await bot.send_message(message.from_user.id, f'Вы изменили свой никнейм на {message.text}')
            elif '@' in message.text or '/' in message.text:
                await bot.send_message(message.from_user.id, 'Ваш никнейм содержит запрещенные символы')
            else:
                await bot.send_message(message.from_user.id, 'Никнейм может состоять максимум из 11 символов')
        elif db_post.get_action(message.from_user.id) == 'transfer_1':
            valid_check = "^\\+?[1-9][0-9]{7,14}$"
            if len(message.text) == 11 or len(message.text) == 12:
                if re.match(valid_check, message.text) is not None:
                    if message.text == db_post.get_phone(message.from_user.id):
                        await bot.send_message(message.from_user.id, 'Вы не можете переводить деньги себе')
                    elif db_post.phone_exists(message.text) is False:
                        await bot.send_message(message.from_user.id, 'Адресата с таким номером не существует')
                    else:
                        with open('file.txt', 'w') as file:
                            file.write(message.text)
                        db_post.set_action(message.from_user.id, 'transfer_2')
                        await bot.send_message(message.from_user.id, f'Получатель: {db_post.get_user_by_phone(message.text)}')
                        await bot.send_message(message.from_user.id, 'Введите сумму')
                else:
                    await bot.send_message(message.from_user.id, 'Введите номер без пробелов и дефисов')
            else:
                await bot.send_message(message.from_user.id, 'Вы ввели недопустимое количество цифр')
        elif db_post.get_action(message.from_user.id) == 'transfer_2':
            try:
                if db_post.get_balance(message.from_user.id) < float(message.text):
                    await bot.send_message(message.from_user.id, 'У вас недостаточно средств')
                elif float(message.text) < 0:
                    await bot.send_message(message.from_user.id, 'Вы не можете вводить отрицательные числа')
                elif float(message.text) < 150:
                    await bot.send_message(message.from_user.id, 'Минимальная сумма для перевода составляет 150')
                elif float(message.text) > 1000000:
                    await bot.send_message(message.from_user.id, 'Максимальная сумма для перевода составляет 1,000,000')
                elif Decimal(str(float(message.text))).as_tuple().exponent * (-1) > 2:
                    await bot.send_message(message.from_user.id, 'Вы можете ввести только 2 числа после запятой')
                else:
                    with open('file.txt', 'r') as file:
                        phone = file.read()
                    balance = float(message.text)
                    db_post.transfer(message.from_user.id, phone, balance)
                    db_post.set_action(message.from_user.id, 'done')
                    db_post.set_transaction_info(db_post.get_nickname(message.from_user.id), db_post.get_user_by_phone(phone), balance, message.date)
                    await bot.send_message(db_post.get_user_id_by_phone(phone), db_post.notification(message.from_user.id, balance))
                    await bot.send_message(message.from_user.id, 'Транзакция успешно произведена!')
            except Exception:
                await bot.send_message(message.from_user.id, 'Введите число корректно')
        else:
            await bot.send_message(message.from_user.id, 'Неизвестная команда')
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
