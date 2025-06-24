import os
import logging
import io
import matplotlib.pyplot as plt
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import URLInputFile

# ========================================================
# КОНФИГУРАЦИЯ ДЛЯ DEPLOY НА RENDER.COM
# ========================================================

# Получаем токен из переменных окружения Render
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not BOT_TOKEN:
    logging.critical("❌ TELEGRAM_TOKEN не найден в переменных окружения!")
    logging.critical("Добавьте токен в настройках Render: Environment Variables")
    exit(1)

# Остальные настройки
AR_COST = 500000  # Базовая стоимость внедрения AR
PORT = int(os.environ.get('PORT', 5000))  # Для webhook (если понадобится)

# ========================================================
# КОНСТАНТЫ И НАСТРОЙКИ БОТА
# ========================================================

# Коэффициенты для разных категорий
CATEGORY_COEFFS = {
    "одежда": {"conversion_increase": 0.25, "return_reduction": 0.35, "icon": "👕"},
    "мебель": {"conversion_increase": 0.15, "return_reduction": 0.25, "icon": "🛋️"},
    "электроника": {"conversion_increase": 0.20, "return_reduction": 0.15, "icon": "📱"},
    "косметика": {"conversion_increase": 0.30, "return_reduction": 0.40, "icon": "💄"},
    "другое": {"conversion_increase": 0.18, "return_reduction": 0.20, "icon": "📦"}
}

class CalcStates(StatesGroup):
    AVERAGE_CHECK = State()
    MONTHLY_ORDERS = State()
    CONVERSION = State()
    RETURN_RATE = State()
    PRODUCT_CATEGORY = State()

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========================================================
# ОСНОВНЫЕ ОБРАБОТЧИКИ КОМАНД
# ========================================================

@dp.message(F.text == "/start")
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Привет! Я ваш AR-консультант от Arigami. Помогу рассчитать, "
        "сколько вы сэкономите с дополненной реальностью.\n\n"
        "Давайте за 2 минуты оценим ваш потенциал!\n"
        "➡️ Укажите *средний чек* заказа в рублях (например: 8500):",
        parse_mode="Markdown"
    )
    await state.set_state(CalcStates.AVERAGE_CHECK)

@dp.message(CalcStates.AVERAGE_CHECK)
async def process_average_check(message: types.Message, state: FSMContext):
    try:
        value = float(message.text.replace(",", "."))
        if value <= 0:
            raise ValueError
        await state.update_data(average_check=value)
        await message.answer(
            "✓ Отлично! Теперь укажите *количество заказов в месяц*:",
            parse_mode="Markdown"
        )
        await state.set_state(CalcStates.MONTHLY_ORDERS)
    except:
        await message.answer("⚠️ Пожалуйста, введите сумму числом (например: 4500)")

@dp.message(CalcStates.MONTHLY_ORDERS)
async def process_monthly_orders(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError
        await state.update_data(monthly_orders=value)
        
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text="❓ Не знаю точный показатель",
            callback_data="conversion_unknown"
        ))
        
        await message.answer(
            "📊 Теперь укажите *текущий процент конверсии* в покупки:\n"
            "(Например: 2.5 или 3%)",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await state.set_state(CalcStates.CONVERSION)

@dp.callback_query(F.data == "conversion_unknown")
async def unknown_conversion(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(conversion=2.0)
    await callback.message.answer(
        "✅ Установлено значение 2% (средний показатель).\n\n"
        "Теперь укажите *процент возвратов* товаров (например: 15%):",
        parse_mode="Markdown"
    )
    await state.set_state(CalcStates.RETURN_RATE)
    await callback.answer()

@dp.message(CalcStates.CONVERSION)
async def process_conversion(message: types.Message, state: FSMContext):
    try:
        value = float(message.text.replace("%", "").replace(",", "."))
        if not 0.1 <= value <= 100:
            raise ValueError
        await state.update_data(conversion=value)
        await message.answer(
            "🔄 Теперь укажите *процент возвратов* товаров (например: 15%):",
            parse_mode="Markdown"
        )
        await state.set_state(CalcStates.RETURN_RATE)
    except:
        await message.answer("⚠️ Пожалуйста, введите процент числом (например: 3.4)")

@dp.message(CalcStates.RETURN_RATE)
async def process_return_rate(message: types.Message, state: FSMContext):
    try:
        value = float(message.text.replace("%", "").replace(",", "."))
        if not 1 <= value <= 100:
            raise ValueError
        
        await state.update_data(return_rate=value)
        
        builder = InlineKeyboardBuilder()
        for category, params in CATEGORY_COEFFS.items():
            builder.add(types.InlineKeyboardButton(
                text=f"{params['icon']} {category.capitalize()}",
                callback_data=f"category_{category}"
            ))
        builder.adjust(2)
        
        await message.answer(
            "📦 Выберите *категорию товаров*:",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        await state.set_state(CalcStates.PRODUCT_CATEGORY)
    except:
        await message.answer("⚠️ Пожалуйста, введите процент числом (например: 15)")

@dp.callback_query(F.data.startswith("category_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    await state.update_data(product_category=category)
    data = await state.get_data()
    
    # Расчет результатов
    results = calculate_roi(data)
    report_text = format_report(results, data)
    chart = generate_roi_chart(results)
    
    # Отправка результатов
    await callback.message.answer_photo(
        photo=types.BufferedInputFile(chart.getvalue(), filename="roi_chart.png"),
        caption=report_text,
        parse_mode="Markdown"
    )
    
    # Дополнительные опции
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="📥 Скачать детальный отчет",
            callback_data="get_full_report"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="💬 Бесплатная консультация",
            url="https://arigami.io/contact"
        ),
        types.InlineKeyboardButton(
            text="🔄 Новый расчет",
            callback_data="new_calculation"
        )
    )
    
    await callback.message.answer(
        "Хотите получить персональное предложение или обсудить внедрение AR?",
        reply_markup=builder.as_markup()
    )
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "new_calculation")
async def new_calculation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🔁 Начнем новый расчет!")
    await start_cmd(callback.message, state)

# ========================================================
# ФУНКЦИИ РАСЧЕТА И ОТЧЕТНОСТИ
# ========================================================

def calculate_roi(data):
    coeffs = CATEGORY_COEFFS[data['product_category']]
    
    # Дополнительные заказы
    additional_orders = data['monthly_orders'] * (data['conversion'] / 100) * coeffs['conversion_increase']
    additional_revenue = additional_orders * data['average_check'] * 12
    
    # Экономия на возвратах
    returns_reduction = data['monthly_orders'] * (data['return_rate'] / 100) * coeffs['return_reduction']
    savings_on_returns = returns_reduction * data['average_check'] * 12
    
    # Общая выгода
    total_benefit = additional_revenue + savings_on_returns
    
    # ROI расчет
    roi_percent = ((total_benefit - AR_COST) / AR_COST) * 100
    payback_months = AR_COST / (total_benefit / 12) if total_benefit > 0 else 999
    
    return {
        "additional_revenue": additional_revenue,
        "savings_on_returns": savings_on_returns,
        "total_benefit": total_benefit,
        "ar_cost": AR_COST,
        "roi_percent": roi_percent,
        "payback_months": payback_months,
        "category": data['product_category']
    }

def format_report(results, data):
    category_icon = CATEGORY_COEFFS[results['category']]['icon']
    category_name = results['category'].capitalize()
    
    report = (
        f"{category_icon} *Результаты расчета для {category_name}*\n\n"
        f"🔍 На основе ваших данных:\n"
        f"- Средний чек: {data['average_check']:,.0f} ₽\n"
        f"- Заказов/мес: {data['monthly_orders']}\n"
        f"- Конверсия: {data['conversion']}%\n"
        f"- Возвраты: {data['return_rate']}%\n\n"
        f"💸 *Годовая экономия с AR:*\n"
        f"▸ Доп. доход: +{results['additional_revenue']:,.0f} ₽\n"
        f"▸ Экономия на возвратах: +{results['savings_on_returns']:,.0f} ₽\n"
        f"▸ Затраты на AR: -{results['ar_cost']:,.0f} ₽\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 *Чистая выгода: {results['total_benefit'] - results['ar_cost']:,.0f} ₽*\n\n"
        f"📊 ROI: *{results['roi_percent']:.1f}%*\n"
        f"⏱ Окупаемость: *{results['payback_months']:.1f} мес.*\n\n"
        f"_Расчеты основаны на реальных кейсах клиентов Arigami_"
    )
    
    return report

def generate_roi_chart(results):
    plt.style.use('seaborn-v0_8-darkgrid')
    
    labels = ['Доп. доход', 'Экономия', 'Затраты']
    values = [
        results['additional_revenue'],
        results['savings_on_returns'],
        results['ar_cost']
    ]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, values, color=['#4CAF50', '#2196F3', '#FF9800'])
    
    ax.set_title('Распределение экономии (год)', fontsize=14, pad=20)
    ax.set_ylabel('Рубли', fontsize=12)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Добавление значений на столбцы
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:,.0f} ₽',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

@dp.callback_query(F.data == "get_full_report")
async def send_full_report(callback: types.CallbackQuery):
    # В реальности здесь генерация PDF
    report_image = URLInputFile("https://arigami.io/images/ar-roi-report-sample.png")
    
    await callback.message.answer_photo(
        photo=report_image,
        caption="📊 Вот как будет выглядеть ваш персональный отчет. "
                "Для получения полной версии оставьте контакты на сайте 👇",
        reply_markup=InlineKeyboardBuilder().add(
            types.InlineKeyboardButton(
                text="🚀 Получить отчет на почту",
                url="https://arigami.io/roi-report"
            )
        ).as_markup()
    )
    await callback.answer()

# ========================================================
# ЗАПУСК БОТА ДЛЯ DEPLOY НА RENDER
# ========================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.info("✅ Бот запущен успешно")
    logging.info(f"🆔 ID бота: {bot.id}")
    
    # Для Render.com - используем polling
    dp.run_polling(bot)
