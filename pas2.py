# midworld_bot.py
import telebot
from telebot import types
import os
import json

# -------------------------
# تنظیمات اولیه
# -------------------------
TOKEN = "7897845917:AAH_C6iPYEJ6GQP6jcXq5ZgSRA5DGhQTBIY"  # <-- اینو عوض کن
ADMINS = {7281641070,7270786778}  # <-- آیدی تلگرام ادمین‌ها رو اینجا بذار (مثال: {7281641070})
DATA_FOLDER = "data_midworld"

# -------------------------
# ثابت‌ها و دسته‌ها
# -------------------------
CATEGORIES = [
    "افراد نظامی","نیروی ویژه", "اژدهایان", "کمیاب ها", "قهرمانان", "شاغل ها",
    "تسلیحات جنگی", "تله", "جمعیت", "عتیقه فروشی", "خزانه",
    "آیتم", "انبار", "سازه ها"
]

# -------------------------
# ساختار داده برای هر گروه
# هر دسته به یکی از شکل‌های زیر نگهداری میشه:
# - معمولا dict از نام_آیتم -> عدد
# - برای "سازه ها": dict از نام_سازه -> {"تعداد":int,"ظرفیت":int,"ظرفیت اشغال شده":int}
# -------------------------

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def group_file(chat_id):
    return os.path.join(DATA_FOLDER, f"{chat_id}.json")

def get_group_data(chat_id):
    path = group_file(chat_id)
    if not os.path.exists(path):
        # ساختار اولیه: هر دسته یه دیکشن خالی
        data = {cat: {} for cat in CATEGORIES}
        data["افراد نظامی"] = {
            "کماندار": 0,
            "نگهبان": 0,
            "دریانورد": 0,
            "فیدل": 0,
            "زوال": 0,
            
            "کوتوله بربری": 0,
            "کوتوله کلاه قیفی": 0,
            "کوتوله پشمی": 0,
            "کوتوله برفی": 0,
            "کوتوله قاتل":0,
            "سر شکن": 0,
            
            "غول بومی": 0,
            "پیرسالار": 0,
            "غول جمجمه": 0,
            "پروجیوس": 0,
            "آسورا": 0, 
            "شوالیه سنگدل": 0,
            "شوالیه قدیسان": 0,
            "شوالیه آهنین": 0,
            "شوالیه شیر طلایی": 0,
            "ملئوداس خونخوار": 0,
            "روحانی بی صدا": 0,
            "جنگ سالار": 0,
            "شوالیه برتانی": 0,
            "شهسوار رودشار": 0
        }

        data["نیروی ویژه"] = {}
        
        data["اژدهایان"]={}
        
        data["کمیاب ها"]={}
        
        data["قهرمانان"]={}

        data["سازه ها"] = {}
        
        save_group_data(chat_id, data)
        return data
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_group_data(chat_id, data):
    path = group_file(chat_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------------
# حالت‌های موقت گفتگو برای پیگیری مراحل ویرایش
# ساختار: STATES[chat_id] = {"mode": ..., "sub": ..., "category": ..., "item": ...}
# -------------------------
STATES = {}

def set_state(chat_id, **kwargs):
    s = STATES.get(str(chat_id), {})
    s.update(kwargs)
    STATES[str(chat_id)] = s

def clear_state(chat_id):
    if str(chat_id) in STATES:
        del STATES[str(chat_id)]

def get_state(chat_id):
    return STATES.get(str(chat_id), {})

# -------------------------
# ابزارهای کمکی نمایش
# -------------------------
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("دارایی", "ویرایش")
    return markup

def categories_keyboard(add_back=True):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # اضافه کردن در چند ستون
    row = []
    for i, cat in enumerate(CATEGORIES, start=1):
        row.append(cat)
        # add two per row (or 3) — اما resize_keyboard باعث میشه مرتب نمایش داده بشه
        if len(row) >= 2:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)
    if add_back:
        markup.add("بازگشت 🔙")
    return markup

def back_keyboard():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("بازگشت 🔙")
    return m

def edit_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("کاهش", "افزایش")
    markup.add("اضافه کردن آیتم جدید")
    markup.add("بازگشت 🔙")
    return markup

def feature_keyboard():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("تعداد", "ظرفیت")
    m.add("ظرفیت اشغال شده")
    m.add("بازگشت 🔙")
    return m

# -------------------------
# فرمت نمایش لیست‌ها
# -------------------------
def format_category_list(data, category):
    # data: گروه
    catdata = data.get(category, {})
    if category == "سازه ها":
        if not catdata:
            return "لیست سازه‌ها خالی است."
        lines = []
        for name, attrs in catdata.items():
            lines.append(f"{name} — تعداد: {attrs.get('تعداد',0)}, ظرفیت: {attrs.get('ظرفیت',0)}, ظرفیت اشغال شده: {attrs.get('ظرفیت اشغال شده',0)}")
        return "\n".join(lines)
    elif category == "جمعیت":
        # نمایش جمعیت خلاصه — ولی در منوی دارایی وقتی کاربر روی جمعیت کلیک کند،
        # خواستی چهار تا گزینه نمایش داده بشن: جمعیت کل، جمعیت نظامی، جمعیت شاغل، جمعیت قهرمانان
        # این تابع عادی مصرف نمیشه برای گزینه‌های جمعیت تفصیلی.
        return "برای مشاهده‌ی جزئیات جمعیت از منوی جمعیت استفاده کنید."
    else:
        if not catdata:
            return f"لیست {category} خالی است."
        lines = []
        for name, count in catdata.items():
            lines.append(f"{name} — تعداد: {count}")
        return "\n".join(lines)

# -------------------------
# محاسبه‌ی جمعیت برای نمایش خلاصه
# فرض: داده‌های "شاغل ها", "افراد نظامی", "قهرمانان" به شکل name->count هستند.
# -------------------------
def compute_population_summary(data):
    military = sum(int(v) for v in data.get("افراد نظامی", {}).values()) if data.get("افراد نظامی") else 0
    employed = sum(int(v) for v in data.get("شاغل ها", {}).values()) if data.get("شاغل ها") else 0
    heroes = sum(int(v) for v in data.get("قهرمانان", {}).values()) if data.get("قهرمانان") else 0
    total = military + employed + heroes
    return {
        "جمعیت کل": total,
        "جمعیت نظامی": military,
        "جمعیت افراد شاغل": employed,
        "جمعیت قهرمانان": heroes
    }

# -------------------------
# بوت و هندلرها
# -------------------------
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def start_handler(message):
    chat_id = message.chat.id
    # ایجاد فایل گروهی در صورت نیاز
    get_group_data(chat_id)
    clear_state(chat_id)

    bot.send_message(chat_id, "سلام، به دنیای میانی خوش آمدید.", reply_markup=main_keyboard())

# نمایش منوی دارایی
@bot.message_handler(func=lambda m: m.text == "دارایی")
def show_assets(message):
    chat_id = message.chat.id
    set_state(chat_id, mode="view_assets")
    bot.send_message(chat_id, "لطفا لیست دارایی مورد نظر را انتخاب کنید:", reply_markup=categories_keyboard())

# نمایش منوی ویرایش (فقط برای ادمین)
@bot.message_handler(func=lambda m: m.text == "ویرایش")
def show_edit(message):
    chat_id = message.chat.id
    uid = message.from_user.id
    if uid not in ADMINS:
        bot.send_message(chat_id, "❌ شما دسترسی به ویرایش ندارید.", reply_markup=main_keyboard())
        return
    set_state(chat_id, mode="edit_main")
    bot.send_message(chat_id, "لطفا نوع ویرایش را انتخاب کنید:", reply_markup=edit_main_keyboard())

# بازگشت
@bot.message_handler(func=lambda m: m.text == "بازگشت 🔙")
def go_back(message):
    chat_id = message.chat.id
    clear_state(chat_id)
    bot.send_message(chat_id, "بازگشت به منوی اصلی.", reply_markup=main_keyboard())

# وقتی کاربر یک دسته را انتخاب می‌کند (در حالت دارایی یا ویرایش)
@bot.message_handler(func=lambda m: m.text in CATEGORIES)
def category_selected(message):
    chat_id = message.chat.id
    cat = message.text
    state = get_state(chat_id).get("mode")
    data = get_group_data(chat_id)

    # حالت مشاهده / دارایی
    if state == "view_assets":
        if cat == "جمعیت":
            # نمایش چهار گزینه جمعیت
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("جمعیت کل", "جمعیت نظامی")
            markup.add("جمعیت افراد شاغل", "جمعیت قهرمانان")
            markup.add("بازگشت 🔙")
            set_state(chat_id, mode="view_population_options")
            bot.send_message(chat_id, "انتخاب کنید کدام جمعیت را می‌خواهید مشاهده کنید:", reply_markup=markup)
            return
        # سازه‌ها یا بقیه دسته‌ها
        text = format_category_list(data, cat)
        bot.send_message(chat_id, text, reply_markup=categories_keyboard())
        return

    # حالت ویرایش: کاربر انتخاب کرده چه نوع ویرایش (کاهش/افزایش/اضافه)
    if state == "edit_choose_list":
        # این حالت زمانی تنظیم میشه که کاربر "کاهش" یا "افزایش" رو انتخاب کنه
        action = get_state(chat_id).get("action")  # "decrease" یا "increase"
        if cat == "سازه ها":
            # تغییر ویژگی‌های سازه
            set_state(chat_id, mode="edit_struct_feature", action=action)
            bot.send_message(chat_id, "کدام ویژگی را میخواهید تغییر دهید؟", reply_markup=feature_keyboard())
            return
        else:
            # برای سایر دسته‌ها می‌پرسیم کدام آیتم را میخواهی تغییر بده (اسم آیتم)
            set_state(chat_id, mode="edit_choose_item", action=action, category=cat)
            bot.send_message(chat_id, f"نام آیتمی که در لیست «{cat}» می‌خواهید تغییر دهید را بنویسید (یا از لیست انتخاب کنید):", reply_markup=types.ForceReply(selective=False))
            return

    # حالت اضافه کردن آیتم جدید
    if state == "edit_add_item":
        if cat == "سازه ها":
            set_state(chat_id, mode="edit_add_struct", category="سازه ها")
            bot.send_message(chat_id, "اسم آیتم جدید سازه را بنویسید:", reply_markup=types.ForceReply(selective=False))
            return
        else:
            set_state(chat_id, mode="edit_add_item_name", category=cat)
            bot.send_message(chat_id, f"نام آیتم جدید برای دسته «{cat}» را بنویسید:", reply_markup=types.ForceReply(selective=False))
            return

    # حالت انتخاب برای نمایش ساختارِ سازه یا سایر دسته‌ها در منوهای دیگر
    # fallback:
    bot.send_message(chat_id, "عملیات فعلی نامشخص است. از منوی اصلی شروع کنید.", reply_markup=main_keyboard())
    clear_state(chat_id)

# وقتی کاربر یکی از گزینه‌های جمعیت رو انتخاب می‌کنه (در حالت view_population_options)
@bot.message_handler(func=lambda m: m.text in ["جمعیت کل", "جمعیت نظامی", "جمعیت افراد شاغل", "جمعیت قهرمانان"])
def population_option_selected(message):
    chat_id = message.chat.id
    state = get_state(chat_id).get("mode")
    if state != "view_population_options":
        bot.send_message(chat_id, "ابتدا از منوی دارایی وارد شوید.", reply_markup=main_keyboard())
        return
    data = get_group_data(chat_id)
    summary = compute_population_summary(data)
    key = message.text
    value = summary.get(key, 0)
    # برای جمعیت کل میخوایم جلویش مجموع هم نشون بدیم (که خودش total هست)
    bot.send_message(chat_id, f"{key}: {value}", reply_markup=categories_keyboard())

# هندلر دکمه‌های ویرایش اصلی: "کاهش", "افزایش", "اضافه کردن آیتم جدید"
@bot.message_handler(func=lambda m: m.text in ["کاهش", "افزایش", "اضافه کردن آیتم جدید"])
def edit_action_selected(message):
    chat_id = message.chat.id
    uid = message.from_user.id
    if uid not in ADMINS:
        bot.send_message(chat_id, "❌ شما دسترسی به ویرایش ندارید.", reply_markup=main_keyboard())
        return
    text = message.text
    if text == "کاهش":
        set_state(chat_id, mode="edit_choose_list", action="decrease")
        bot.send_message(chat_id, "ویرایش شما در مورد کدام لیست است؟", reply_markup=categories_keyboard())
        return
    if text == "افزایش":
        set_state(chat_id, mode="edit_choose_list", action="increase")
        bot.send_message(chat_id, "ویرایش شما در مورد کدام لیست است؟", reply_markup=categories_keyboard())
        return
    if text == "اضافه کردن آیتم جدید":
        set_state(chat_id, mode="edit_add_item")
        bot.send_message(chat_id, "به کدام دسته آیتم اضافه شود؟", reply_markup=categories_keyboard())

# حالا هندلر پیام‌های متنی برای مراحل بعدی (نام آیتم، عدد، انتخاب ویژگی سازه و...)
@bot.message_handler(func=lambda m: True, content_types=['text'])
def text_handler(message):
    chat_id = message.chat.id
    text = message.text.strip()
    state = get_state(chat_id).get("mode")

    # اگر حالت None => نادیده یا منوی اصلی
    if not state or state == "view_assets":
        # اگر کاربر اسم یکی از دسته‌ها رو زده ولی حالت اشتباهه، بهش راهنمایی بده
        if text in CATEGORIES:
            # فِشرده‌شده در دسته‌ها با handler دسته‌ها در بالا؛ اینجا فقط fallback
            bot.send_message(chat_id, "از منوها استفاده کنید یا گزینه دارایی را بزنید.", reply_markup=categories_keyboard())
            return
        bot.send_message(chat_id, "برای شروع از منوی اصلی استفاده کنید.", reply_markup=main_keyboard())
        return

    # ---------------------------
    # حالت انتخاب نام آیتم برای افزایش/کاهش (غیر سازه)
    # ---------------------------
    if state == "edit_choose_item":
        category = get_state(chat_id).get("category")
        action = get_state(chat_id).get("action")
        # ذخیره نام آیتم انتخاب شده (اگر وجود نداره بهش میگیم وجود نداره)
        data = get_group_data(chat_id)
        catdata = data.get(category, {})
        # اگر آیتم موجود نیست، به کاربر اخطار بده
        if text not in catdata:
            bot.send_message(chat_id, f"آیتم «{text}» در دسته «{category}» وجود ندارد.\nاگر میخواهید آیتم جدید اضافه کنید از منوی ویرایش -> اضافه کردن آیتم جدید استفاده کنید.", reply_markup=categories_keyboard())
            clear_state(chat_id)
            return
        set_state(chat_id, mode="edit_amount_entry", category=category, item=text, action=action)
        if action == "decrease":
            bot.send_message(chat_id, f"چه تعداد از «{text}» می‌خواهید کم کنید؟", reply_markup=types.ForceReply(selective=False))
        else:
            bot.send_message(chat_id, f"چه تعداد از «{text}» می‌خواهید اضافه کنید؟", reply_markup=types.ForceReply(selective=False))
        return

    # ---------------------------
    # حالت ورود تعداد برای افزایش/کاهش (غیر سازه)
    # ---------------------------
    if state == "edit_amount_entry":
        info = get_state(chat_id)
        category = info.get("category")
        item = info.get("item")
        action = info.get("action")
        data = get_group_data(chat_id)
        try:
            num = int(text)
            if num < 0:
                raise ValueError
        except:
            bot.send_message(chat_id, "لطفاً یک عدد صحیح مثبت وارد کنید.", reply_markup=types.ForceReply(selective=False))
            return
        if category == "سازه ها":
            # این مسیر نباید اینجا بیاد چون سازه‌ها جدا هندل میشن
            bot.send_message(chat_id, "برای ویرایش سازه‌ها باید ویژگی مورد نظر را انتخاب کنید.", reply_markup=main_keyboard())
            clear_state(chat_id)
            return
        # اعمال تغییر
        current = int(data.get(category, {}).get(item, 0))
        if action == "decrease":
            new = max(0, current - num)
        else:
            new = current + num
        data[category][item] = new
        save_group_data(chat_id, data)
        bot.send_message(chat_id, f"تعداد آیتم «{item}» در دسته «{category}» اکنون {new} است.", reply_markup=categories_keyboard())
        clear_state(chat_id)
        return

    # ---------------------------
    # حالت انتخاب ویژگی سازه (تعداد / ظرفیت / ظرفیت اشغال شده)
    # مربوط به کاهش/افزایش سازه
    # ---------------------------
    if state == "edit_struct_feature":
        feature = text  # باید یکی از سه ویژگی باشه
        if feature not in ["تعداد", "ظرفیت", "ظرفیت اشغال شده"]:
            bot.send_message(chat_id, "لطفا یکی از گزینه‌های موجود را انتخاب کنید.", reply_markup=feature_keyboard())
            return
        action = get_state(chat_id).get("action")
        set_state(chat_id, mode="edit_struct_choose_item", feature=feature, action=action)
        bot.send_message(chat_id, "کدام آیتم لیست سازه را میخواهید ویرایش کنید؟ (اسم را بنویسید)", reply_markup=types.ForceReply(selective=False))
        return

    # ---------------------------
    # حالت انتخاب نام سازه برای ویرایش ویژگی
    # ---------------------------
    if state == "edit_struct_choose_item":
        feature = get_state(chat_id).get("feature")
        action = get_state(chat_id).get("action")
        data = get_group_data(chat_id)
        structs = data.get("سازه ها", {})
        if text not in structs:
            bot.send_message(chat_id, f"سازه‌ای به نام «{text}» وجود ندارد.\nاگر می‌خواهید سازه جدید اضافه کنید از گزینه 'اضافه کردن آیتم جدید' استفاده کنید.", reply_markup=categories_keyboard())
            clear_state(chat_id)
            return
        set_state(chat_id, mode="edit_struct_amount", item=text, feature=feature, action=action)
        bot.send_message(chat_id, f"چه مقدار می‌خواهید {'کم' if action=='decrease' else 'اضافه'} کنید برای ویژگی «{feature}» سازه «{text}»؟", reply_markup=types.ForceReply(selective=False))
        return

    # ---------------------------
    # حالت ورود عدد برای سازه
    # ---------------------------
    if state == "edit_struct_amount":
        info = get_state(chat_id)
        item = info.get("item")
        feature = info.get("feature")
        action = info.get("action")
        data = get_group_data(chat_id)
        try:
            num = int(text)
        except:
            bot.send_message(chat_id, "لطفاً یک عدد صحیح وارد کنید.", reply_markup=types.ForceReply(selective=False))
            return
        if item not in data.get("سازه ها", {}):
            bot.send_message(chat_id, "سازه پیدا نشد.", reply_markup=categories_keyboard())
            clear_state(chat_id)
            return
        current = int(data["سازه ها"][item].get(feature, 0))
        if action == "decrease":
            new = current - num
            if new < 0:
                new = 0
        else:
            new = current + num
        data["سازه ها"][item][feature] = new
        save_group_data(chat_id, data)
        bot.send_message(chat_id, f"ویژگی «{feature}» سازه «{item}» اکنون {new} است.", reply_markup=categories_keyboard())
        clear_state(chat_id)
        return

    # ---------------------------
    # حالت اضافه کردن آیتم جدید (غیر سازه): انتظار نام آیتم
    # ---------------------------
    if state == "edit_add_item_name":
        category = get_state(chat_id).get("category")
        name = text
        data = get_group_data(chat_id)
        if name in data.get(category, {}):
            bot.send_message(chat_id, f"آیتم «{name}» قبلاً در دسته «{category}» وجود دارد.", reply_markup=categories_keyboard())
            clear_state(chat_id)
            return
        # اضافه کن با مقدار 0
        data[category][name] = 0
        save_group_data(chat_id, data)
        bot.send_message(chat_id, f"آیتم «{name}» به دسته «{category}» اضافه شد با مقدار اولیه 0.", reply_markup=categories_keyboard())
        clear_state(chat_id)
        return

    # ---------------------------
    # حالت اضافه کردن سازه جدید: انتظار اسم سازه سپس مقداردهی صفر برای تمام ویژگی‌ها
    # ---------------------------
    if state == "edit_add_struct":
        name = text
        data = get_group_data(chat_id)
        if name in data.get("سازه ها", {}):
            bot.send_message(chat_id, f"سازه «{name}» قبلاً وجود دارد.", reply_markup=categories_keyboard())
            clear_state(chat_id)
            return
        data["سازه ها"][name] = {"تعداد":0, "ظرفیت":0, "ظرفیت اشغال شده":0}
        save_group_data(chat_id, data)
        bot.send_message(chat_id, f"سازه «{name}» اضافه شد (تعداد=0، ظرفیت=0، ظرفیت اشغال شده=0).", reply_markup=categories_keyboard())
        clear_state(chat_id)
        return

    # ---------------------------
    # حالت پیش‌بینی نشده یا اشتباه
    # ---------------------------
    bot.send_message(chat_id, "عملیات نامشخص یا منقضی شده — لطفاً دوباره از منوی ویرایش یا دارایی شروع کنید.", reply_markup=main_keyboard())
    clear_state(chat_id)


# -------------------------
# راهنمایی: نمایش لیست یک دسته با دستور /show <دسته>
# (اختیاری، برای تست سریع)
# -------------------------
@bot.message_handler(commands=["show"])
def cmd_show(message):
    chat_id = message.chat.id
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(chat_id, "دستور: /show <نام دسته>\nبرای نمونه: /show سازه ها", reply_markup=main_keyboard())
        return
    cat = parts[1].strip()
    if cat not in CATEGORIES:
        bot.send_message(chat_id, "نام دسته معتبر نیست.", reply_markup=main_keyboard())
        return
    data = get_group_data(chat_id)
    bot.send_message(chat_id, format_category_list(data, cat), reply_markup=categories_keyboard())

# -------------------------
# اجرای ربات
# -------------------------
if __name__ == "__main__":
    print("Bot is polling...")
    bot.infinity_polling(timeout=60, long_polling_timeout = 5)
