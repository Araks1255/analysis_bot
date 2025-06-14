import io
import asyncio

from aiogram.filters import StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import F, Router
from aiogram.types import Message

import google.generativeai as genai

from aiohttp import ClientSession, FormData, ClientTimeout

from config import SECRET_WORD, API_KEY

import app.keyboards as kb

genai.configure(api_key=API_KEY)

router = Router()

class SpendingAnalysis(StatesGroup):
    check_secret_word = State()
    get_photo = State()
    text_parsing_check = State()
    
@router.message(StateFilter(None), F.text == "Анализ трат")
async def start_spending_analysis(message: Message, state: FSMContext):
    await message.answer(
        "введите секретное слово (если вы проверяющий т-банка, то найдёте его в презентации)",
        reply_markup=kb.cancel
    )
    await state.set_state(SpendingAnalysis.check_secret_word)
    
@router.message(StateFilter(SpendingAnalysis), F.text == "Отмена")
async def cancel(message: Message, state: FSMContext):
    await message.answer("Ладно", reply_markup=kb.main)
    await state.clear()
    
@router.message(SpendingAnalysis.check_secret_word)
async def check_secret_word(message: Message, state: FSMContext):
    if message.text != SECRET_WORD:
        await message.answer("введено неверное секретное слово")
        return
    
    await message.answer("Пришлите свои расходы за месяц вот в таком формате:")
    await message.answer_photo("AgACAgIAAxkBAAO6aE0fdDHUDffS9W7Vx--oVVQAAQHGAAJM7zEbjRVoSmfX4OTtFgAByQEAAwIAA3gAAzYE")
    await state.set_state(SpendingAnalysis.get_photo)
    
@router.message(SpendingAnalysis.get_photo)
async def get_photo(message: Message, state: FSMContext):    
    try:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        file_name = "image.jpg"
    except:
        try:
            document = message.document
            file = await message.bot.get_file(document.file_id)
            file_name = "image.png"
        except:
            await message.answer("пришлите фото или файл формата png")
            return
            
    placeholer = await message.answer("Один момент...")
    
    buffer = io.BytesIO()
    await message.bot.download_file(file.file_path, destination=buffer)
    
    buffer.seek(0)
    
    form = FormData()
    form.add_field(
        name="file",
        value=buffer,
        filename=file_name,
        content_type="image/jpeg"
    )
    form.add_field("language", "rus")
    
    headers = {"apiKey": "helloworld"}
    
    async with ClientSession() as session:
        async with session.post("https://api.ocr.space/parse/image", data=form, headers=headers, timeout=ClientTimeout(15)) as resp:
            jsonResp = await resp.json()
            
    try:
        await placeholer.edit_text("Результат распознования текста:")
        await message.answer(jsonResp["ParsedResults"][0]["ParsedText"])
        await message.answer(
            "Всё ли верно? Если нет, пришлите исправленную версию (но не меняйте порядок данных), если да - нажмите соответствующую кнопку на клавиатуре",
            reply_markup=kb.yes,
        )
        
        await state.update_data(parsedText=jsonResp["ParsedResults"][0]["ParsedText"])
        await state.set_state(SpendingAnalysis.text_parsing_check)
        
    except asyncio.TimeoutError:
        await message.answer(
            "Сервис для распознавания текста не отвечает. Попробуйте ещё раз позже\n(Он бесплатный, так что такое случается. Но в большинстве случаев всё работает)"
        )
        
    except:
        await message.answer("возникла непредвиденная ошибка", reply_markup=kb.main)
        await state.clear()
        
@router.message(SpendingAnalysis.text_parsing_check)
async def text_parsing_check(message: Message, state: FSMContext):
    if message.text != "Да":
        spending = message.text
    else:
        data = await state.get_data()
        try:
            spending = data["parsedText"]
        except:
            await message.answer("Произошла ошибка при получении результатов распознования текста. Попробуйте отправить его вручную")
            
    placeholder = await message.answer("Один момент...")
   
    prompt = (
        "Ты должен провести аналитику расходов по этим данным, чтобы показать пользователю важность изучения финансовой аналитики"
        f"(данные идут в формате *категория траты_на_категорию*, именно в таком порядке) (ответ обязательно присылай обычным текстом а не markdown разметкой):\n{spending}"
    )
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response =  await model.generate_content_async(prompt)
        await placeholder.edit_text(response.text)
        
    except Exception as ex:
        await message.answer("Произошла непредвиденная ошибка",reply_markup=kb.main)
        print(str(ex))
        
    await state.clear()
    