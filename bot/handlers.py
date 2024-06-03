import random
import math
from aiogram import types, Bot
import aiosqlite
from aiogram import Dispatcher
from config import TOKEN
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup





bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


class Form(StatesGroup):
    question = State()
    answer = State()

@dp.callback_query_handler(lambda call: call.data == 'add')
async def process_add_callback(call: types.CallbackQuery):
    await Form.question.set()
    await bot.send_message(call.message.chat.id, 'Введите вопрос:')

@dp.message_handler(state=Form.question)
async def process_question(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['question'] = message.text

    await Form.next()
    await message.reply("Введите ответ:")

@dp.message_handler(state=Form.answer)
async def process_answer(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        question = data['question']
        answer = message.text

        async with aiosqlite.connect('example.db') as db:
            await db.execute('INSERT INTO qa (question, answer) VALUES (?, ?)', (question, answer))
            await db.commit()

    await state.finish()
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Назад к вопросам", callback_data='back')
    keyboard.add(button)
    await message.reply("Вопрос и ответ сохранены.", reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data == 'randQu')
async def pprocces_random_questions(call: types.CallbackQuery):
    async with aiosqlite.connect('example.db') as db:
        async with db.execute('SELECT question FROM qa') as cursor:
            questions = await cursor.fetchall()
            if questions:
                random_question = random.choice(questions)[0]
                await bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=random_question,
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="Показать ответ", callback_data="show_answer"),
                             InlineKeyboardButton(text="Назад", callback_data='back'),]
                        ]
                    )
                )
            else:
                await bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="Вопросов пока нет."
                )



@dp.callback_query_handler(lambda call: call.data == 'back')
async def process_back_callback(call: types.CallbackQuery):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Рандомный вопрос", callback_data='randQu'))
    markup.row(InlineKeyboardButton("Добавить вопрос", callback_data='add'),
               InlineKeyboardButton("Удалить вопрос", callback_data='del'))
    
    await bot.edit_message_text(
        text="Выберите действие:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

    
    
@dp.callback_query_handler(lambda call: call.data == 'show_answer')
async def process_show_answer_callback(call: types.CallbackQuery):
    async with aiosqlite.connect('example.db') as db:
        async with db.execute('SELECT answer FROM qa WHERE question = ?', (call.message.text,)) as cursor:
            answer = await cursor.fetchone()
            if answer:
                keyboard = types.InlineKeyboardMarkup()  # Corrected line
                but = types.InlineKeyboardButton('Сделать снова', callback_data='randQu') 
                but1 = types.InlineKeyboardButton('Назад', callback_data='back') # Also, corrected the button creation
                keyboard.add(but)
                keyboard.add(but1)
                
                await bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"Ответ: {answer[0]}",
                    reply_markup=keyboard
                )
            else:
                await bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="Ответ на этот вопрос еще не добавлен."
                )
                
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Рандомный вопрос", callback_data='randQu'))
    markup.row(InlineKeyboardButton("Добавить вопрос", callback_data='add'),
               InlineKeyboardButton("Удалить вопрос", callback_data='del'))


    await message.reply("Выберите действие:", reply_markup=markup)

QUESTIONS_PER_PAGE = 5  # Number of questions per page

@dp.callback_query_handler(lambda call: call.data == 'del')
async def show_questions_and_answers(call: types.CallbackQuery):
    await show_page(call.message.chat.id, call.message.message_id, page=1)



async def show_page(chat_id, message_id, page):
    async with aiosqlite.connect('example.db') as db:
        async with db.execute('SELECT COUNT(*) FROM qa') as cursor:
            total_questions = await cursor.fetchone()
            total_questions = total_questions[0]
            total_pages = math.ceil(total_questions / QUESTIONS_PER_PAGE)
            
            async with db.execute('SELECT id, question, answer FROM qa LIMIT ? OFFSET ?', (QUESTIONS_PER_PAGE, (page-1) * QUESTIONS_PER_PAGE)) as cursor:
                rows = await cursor.fetchall()
                
                if rows:
                    markup = InlineKeyboardMarkup()
                    for row in rows:
                        question_id = row[0]
                        question_text = row[1]
                        button_text = f"{question_text[:20]}..." if len(question_text) > 20 else question_text
                        markup.add(InlineKeyboardButton(button_text, callback_data=f"delete:{question_id}"))
                    
                    pagination_buttons = []
                    if page > 1:
                        pagination_buttons.append(InlineKeyboardButton("«", callback_data=f"page:{page-1}:{message_id}"))
                    if page < total_pages:
                        pagination_buttons.append(InlineKeyboardButton("»", callback_data=f"page:{page+1}:{message_id}"))
                    
                    if pagination_buttons:
                        markup.row(*pagination_buttons)
                    
                    # Add a back button
                    markup.add(InlineKeyboardButton("Назад", callback_data="back"))

                    await bot.edit_message_text(
                        text="Выберите вопрос для удаления:",
                        chat_id=chat_id,
                        message_id=message_id,
                        reply_markup=markup
                    )
                else:
                    # If no rows on the current page, check if there are questions on previous pages
                    if page > 1:
                        await show_page(chat_id, message_id, page-1)
                    else:
                        keyboard = InlineKeyboardMarkup()
                        b = InlineKeyboardButton(text="Добавить вопрос", callback_data='add')
                        keyboard.add(b)
                        # Add a back button
                        keyboard.add(InlineKeyboardButton("Назад", callback_data="back"))
                        await bot.edit_message_text(
                            text="Вопросов и ответов пока нет.",
                            chat_id=chat_id,
                            message_id=message_id,
                            reply_markup=keyboard
                        )

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('page:'))
async def paginate_callback(call: types.CallbackQuery):
    data = call.data.split(':')
    page = int(data[1])
    message_id = int(data[2])
    await show_page(call.message.chat.id, message_id, page)
    await call.answer()
    
@dp.callback_query_handler(lambda call: call.data.startswith('delete'))
async def process_delete_callback(call: types.CallbackQuery):
    question_id = int(call.data.split(':')[1])
    async with aiosqlite.connect('example.db') as db:
        await db.execute('DELETE FROM qa WHERE id = ?', (question_id,))
        await db.commit()
    await bot.send_message(call.message.chat.id, "Вопрос и ответ успешно удалены.")


        