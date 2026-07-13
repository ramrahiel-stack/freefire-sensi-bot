import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DEVICE, PLAYSTYLE, FPS, GRAPHICS = range(4)
SETTINGS_DEVICE, SETTINGS_PLAYSTYLE = range(4, 6)
TIPS_SELECT = 6

DEVICES = {
    "iphone": "📱 iPhone",
    "android": "🤖 Android",
    "tablet": "📟 Tablet",
}

DEVICE_NAMES = {
    "iphone 12": "iphone",
    "iphone 13": "iphone",
    "iphone 14": "iphone",
    "iphone 15": "iphone",
    "poco x5": "android",
    "pixel 6a": "android",
    "samsung": "android",
    "tablet": "tablet",
    "ipad": "tablet",
}

PLAYSTYLES = {
    "one_tap": "🎯 One Tap",
    "drag_headshot": "🔥 Drag Headshot",
    "balanced": "⚖️ Balanced",
    "rush": "💨 Rush",
    "sniper": "🔭 Sniper",
}

FPS_OPTIONS = {
    "60": "60 FPS",
    "90": "90 FPS",
    "120": "120 FPS",
}

BASE_SENSITIVITY = {
    "iphone": {
        "one_tap":      {"general": 155, "red_dot": 140, "2x": 110, "4x": 80, "awm": 55, "gyro": 160},
        "drag_headshot":{"general": 148, "red_dot": 135, "2x": 105, "4x": 75, "awm": 52, "gyro": 185},
        "balanced":     {"general": 130, "red_dot": 118, "2x":  95, "4x": 70, "awm": 50, "gyro": 140},
        "rush":         {"general": 172, "red_dot": 155, "2x": 122, "4x": 86, "awm": 58, "gyro": 178},
        "sniper":       {"general": 100, "red_dot":  90, "2x":  75, "4x": 55, "awm": 38, "gyro": 110},
    },
    "android": {
        "one_tap":      {"general": 145, "red_dot": 132, "2x": 105, "4x": 76, "awm": 52, "gyro": 150},
        "drag_headshot":{"general": 138, "red_dot": 128, "2x": 100, "4x": 72, "awm": 49, "gyro": 175},
        "balanced":     {"general": 122, "red_dot": 112, "2x":  90, "4x": 66, "awm": 47, "gyro": 130},
        "rush":         {"general": 162, "red_dot": 145, "2x": 115, "4x": 82, "awm": 54, "gyro": 168},
        "sniper":       {"general":  92, "red_dot":  85, "2x":  70, "4x": 52, "awm": 36, "gyro": 100},
    },
    "tablet": {
        "one_tap":      {"general": 115, "red_dot": 105, "2x":  85, "4x": 62, "awm": 44, "gyro": 120},
        "drag_headshot":{"general": 110, "red_dot": 100, "2x":  80, "4x": 58, "awm": 41, "gyro": 145},
        "balanced":     {"general": 100, "red_dot":  92, "2x":  74, "4x": 55, "awm": 39, "gyro": 108},
        "rush":         {"general": 128, "red_dot": 118, "2x":  95, "4x": 68, "awm": 46, "gyro": 135},
        "sniper":       {"general":  78, "red_dot":  72, "2x":  60, "4x": 45, "awm": 31, "gyro":  85},
    },
}

SHOOT_BUTTON_SIZE = {
    "iphone":  {"one_tap": 40, "drag_headshot": 32, "balanced": 36, "rush": 47, "sniper": 30},
    "android": {"one_tap": 40, "drag_headshot": 32, "balanced": 38, "rush": 47, "sniper": 30},
    "tablet":  {"one_tap": 42, "drag_headshot": 35, "balanced": 40, "rush": 47, "sniper": 32},
}

FPS_MULTIPLIERS = {
    "60":  1.0,
    "90":  0.90,
    "120": 0.82,
}

GRAPHICS_OPTIONS = {
    "smooth":   "1️⃣ Smooth",
    "standard": "2️⃣ Standard",
    "ultra":    "3️⃣ Ultra / Max",
}

GRAPHICS_MULTIPLIERS = {
    "smooth":   1.03,
    "standard": 1.0,
    "ultra":    0.96,
}

TIPS = {
    "one_tap":       "Keep crosshair at head level. Practice peek-shooting.",
    "drag_headshot": "Start aim at chest level, flick upward on fire. Gyro helps.",
    "balanced":      "Great all-round settings. Works for both close and mid-range.",
    "rush":          "High sensitivity for fast close-range plays. Stay unpredictable.",
    "sniper":        "Lower sensitivity for precision. Hold angles and breathe.",
}

DEEP_TIPS = {
    "one_tap": (
        "🎯 *One Tap — Deep Guide*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🧠 *Mindset*\n"
        "One tap is all about pre-aiming. You win the fight before it starts by placing your crosshair exactly where the enemy's head will be.\n\n"
        "📐 *Crosshair Placement*\n"
        "• Always keep aim at head level — never at chest or feet\n"
        "• Pre-aim corners before you peek, not after\n"
        "• Use cover to reposition between shots\n\n"
        "🎮 *In-Game Technique*\n"
        "• Crouch-peek: reduces your hitbox and steadies aim\n"
        "• Don't spray — one shot, reposition, repeat\n"
        "• Use the MP40 or M1887 at close range for near-instant kills\n\n"
        "🏋️ *Training Drill*\n"
        "In training mode, walk toward a dummy and fire exactly one shot at head height. If you need a second shot, your placement was off — reset and repeat.\n\n"
        "⚙️ *Sensitivity Tip*\n"
        "Keep General sensitivity slightly higher so you can snap to the head quickly. Red Dot slightly lower for control after the snap."
    ),
    "drag_headshot": (
        "🔥 *Drag Headshot — Deep Guide*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🧠 *Mindset*\n"
        "Drag headshot is a flick technique. You aim at the body first, then drag upward to the head the instant you fire — it's muscle memory.\n\n"
        "📐 *The Motion*\n"
        "• Start your aim at chest or stomach level\n"
        "• The moment you press fire, drag your thumb upward\n"
        "• The bullet registers at the head if the timing is right\n"
        "• Works best at close-to-medium range\n\n"
        "🌀 *Gyroscope Usage*\n"
        "• Enable gyro and tilt your phone slightly upward as you fire\n"
        "• Gyro sensitivity should be higher than touch sensitivity\n"
        "• Practice the tilt motion until it's instinctive\n\n"
        "🏋️ *Training Drill*\n"
        "Stand 10m from a dummy. Fire 10 shots trying to drag to the head each time. Count headshots. Aim for 7/10 before moving to real matches.\n\n"
        "⚙️ *Sensitivity Tip*\n"
        "Higher gyro sensitivity = easier drag. If you're over-flicking, lower gyro by 5 points at a time until headshots are consistent."
    ),
    "balanced": (
        "⚖️ *Balanced — Deep Guide*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🧠 *Mindset*\n"
        "Balanced play means adapting to every situation — you're not locked into close range or long range. You win by reading the game.\n\n"
        "🔀 *Adapting Your Play*\n"
        "• Close range: spray to the chest, let recoil climb to the head\n"
        "• Mid range: burst fire 3–4 shots, pause, repeat\n"
        "• Long range: single shots with 4x scope, control breathing\n\n"
        "🗺️ *Positioning*\n"
        "• Take fights at distances where your weapon excels\n"
        "• Don't force close-range fights with a sniper — rotate first\n"
        "• Always have cover within one step\n\n"
        "🏋️ *Training Drill*\n"
        "Practice all three ranges in one training session: 5m, 20m, 50m. You should feel comfortable at all three before ranked.\n\n"
        "⚙️ *Sensitivity Tip*\n"
        "Balanced sensitivity is intentionally moderate. If you feel sluggish at close range, raise General by 5. If scoped shots feel jumpy, lower 4x by 5."
    ),
    "rush": (
        "💨 *Rush — Deep Guide*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🧠 *Mindset*\n"
        "Rush is about chaos and aggression. You create pressure so your enemies react to *you* instead of making their own plays.\n\n"
        "⚡ *Entry Techniques*\n"
        "• Always announce your push — throw a grenade or shoot the door first\n"
        "• Jump-peek: jump before entering a room to break enemy aim\n"
        "• Rush from unexpected angles — the second door, not the main one\n\n"
        "🤝 *Team Coordination*\n"
        "• Rush only when a teammate can cover your flank\n"
        "• Call out enemy positions as you push so teammates can assist\n"
        "• Never rush a full-health squad alone — pick off one first\n\n"
        "🏋️ *Training Drill*\n"
        "Drop Pochinok or Clock Tower in Classic mode. Force every fight at close range for a full match. High-risk, high-reward practice.\n\n"
        "⚙️ *Sensitivity Tip*\n"
        "High General sensitivity lets you spin and track fast targets. If you're overshooting enemies, lower it by 3–5 until tracking feels natural."
    ),
    "sniper": (
        "🔭 *Sniper — Deep Guide*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🧠 *Mindset*\n"
        "Snipers control the map. Your job isn't kills — it's denying movement, forcing rotations, and supporting your team from safety.\n\n"
        "📍 *Positioning*\n"
        "• High ground is your best friend — clock towers, rooftops, hills\n"
        "• Always have a secondary weapon for anyone who pushes you\n"
        "• Relocate after every 2 shots so enemies can't pinpoint you\n\n"
        "🎯 *Shot Mechanics*\n"
        "• Lead moving targets — aim slightly ahead of their direction\n"
        "• Hold breath (default: right-side button) before firing with AWM\n"
        "• Shoot between your own footsteps, not during movement\n\n"
        "🏋️ *Training Drill*\n"
        "In training mode, set a dummy to move and practice hitting it at 80m+ range. Focus on one clean shot, not follow-up shots.\n\n"
        "⚙️ *Sensitivity Tip*\n"
        "AWM scope sensitivity should be your lowest setting. Even 1–2 points too high will cause misses at long range. Tune it down until shots land centre-mass."
    ),
}

async def device_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.lower().strip()

    if text in DEVICE_NAMES:
        device = DEVICE_NAMES[text]
        context.user_data["device"] = device

        keyboard = [
            [InlineKeyboardButton(label, callback_data=f"playstyle:{key}")]
            for key, label in PLAYSTYLES.items()
        ]
        await update.message.reply_text(
            f"📱 Device detected: {DEVICES[device]} ✅\n\n"
            "Step 2 of 4 — Select your playstyle:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return PLAYSTYLE

    await update.message.reply_text(
        "❌ Device not found.\n\n"
        "Try typing:\n"
        "iPhone 12\n"
        "Poco X5\n"
        "Pixel 6a\n"
        "Samsung"
    )

    return DEVICE

def generate_sensitivity(device: str, playstyle: str, fps: str, graphics: str = "standard") -> dict:
    base = BASE_SENSITIVITY[device][playstyle]
    multiplier = FPS_MULTIPLIERS[fps] * GRAPHICS_MULTIPLIERS[graphics]
    jitter = lambda: random.randint(-2, 2)
    return {
        key: max(5, min(200, round(val * multiplier) + jitter()))
        for key, val in base.items()
    }


def get_saved(context: ContextTypes.DEFAULT_TYPE) -> tuple:
    prefs = context.user_data.get("preferences", {})
    return prefs.get("device"), prefs.get("playstyle")


# ─── /start ───────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    saved_device, saved_playstyle = get_saved(context)

    if saved_device and saved_playstyle:
                keyboard = [
            [InlineKeyboardButton(
                f"⚡ Use saved: {DEVICES[saved_device]} · {PLAYSTYLES[saved_playstyle]}",
                callback_data="use_saved"
            )],
            *[
                [InlineKeyboardButton(label, callback_data=f"device:{key}")]
                for key, label in DEVICES.items()
            ],
        ]

        text = (
            "🔥 *Free Fire Sensitivity Generator*\n\n"
            "Your saved preferences are shown above — tap to skip ahead to FPS, "
            "or pick a different device below.\n\n"
            "*Step 1 of 4* — Select your device:"
            
        )
    else:
        keyboard = [
            [InlineKeyboardButton(label, callback_data=f"device:{key}")]
            for key, label in DEVICES.items()
        ]

    await update.message.reply_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )
    return DEVICE


async def use_saved(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    saved_device, saved_playstyle = get_saved(context)
    context.user_data["device"] = saved_device
    context.user_data["playstyle"] = saved_playstyle

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"fps:{key}")]
        for key, label in FPS_OPTIONS.items()
    ]
    text = (
        f"Device: *{DEVICES[saved_device]}* ✅\n"
        f"Playstyle: *{PLAYSTYLES[saved_playstyle]}* ✅\n\n"
        "*Step 3 of 4* — Select your FPS:"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return FPS


async def device_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    device_key = query.data.split(":")[1]
    context.user_data["device"] = device_key

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"playstyle:{key}")]
        for key, label in PLAYSTYLES.items()
    ]
    text = (
        f"Device: *{DEVICES[device_key]}* ✅\n\n"
        "*Step 2 of 4* — Select your playstyle:"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return PLAYSTYLE


async def playstyle_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    playstyle_key = query.data.split(":")[1]
    context.user_data["playstyle"] = playstyle_key

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"fps:{key}")]
        for key, label in FPS_OPTIONS.items()
    ]
    device_key = context.user_data["device"]
    text = (
        f"Device: *{DEVICES[device_key]}* ✅\n"
        f"Playstyle: *{PLAYSTYLES[playstyle_key]}* ✅\n\n"
        "*Step 3 of 4* — Select your FPS:"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return FPS


async def fps_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    fps_key = query.data.split(":")[1]
    context.user_data["fps"] = fps_key

    device_key = context.user_data["device"]
    playstyle_key = context.user_data["playstyle"]

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"graphics:{key}")]
        for key, label in GRAPHICS_OPTIONS.items()
    ]
    text = (
        f"Device: *{DEVICES[device_key]}* ✅\n"
        f"Playstyle: *{PLAYSTYLES[playstyle_key]}* ✅\n"
        f"FPS: *{FPS_OPTIONS[fps_key]}* ✅\n\n"
        "*Step 4 of 4* — What graphics do you play on?"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return GRAPHICS


async def graphics_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    graphics_key = query.data.split(":")[1]
    device_key = context.user_data["device"]
    playstyle_key = context.user_data["playstyle"]
    fps_key = context.user_data["fps"]

    sens = generate_sensitivity(device_key, playstyle_key, fps_key, graphics_key)
    shoot_size = SHOOT_BUTTON_SIZE[device_key][playstyle_key]

    s = context.user_data.setdefault("stats", {
        "total": 0, "playstyles": {}, "devices": {}, "fps": {}
    })
    s["total"] += 1
    s["playstyles"][playstyle_key] = s["playstyles"].get(playstyle_key, 0) + 1
    s["devices"][device_key] = s["devices"].get(device_key, 0) + 1
    s["fps"][fps_key] = s["fps"].get(fps_key, 0) + 1

    result_text = (
        f"🔥 *Your Free Fire Sensitivity Settings*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 Device: *{DEVICES[device_key]}*\n"
        f"🎮 Playstyle: *{PLAYSTYLES[playstyle_key]}*\n"
        f"⚡ FPS: *{FPS_OPTIONS[fps_key]}*\n"
        f"🖥 Graphics: *{GRAPHICS_OPTIONS[graphics_key]}*\n"
        f"🚀 High FPS Mode: ✅ On\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 General: `{sens['general']}`\n"
        f"🔴 Red Dot: `{sens['red_dot']}`\n"
        f"🔭 2x Scope: `{sens['2x']}`\n"
        f"🔬 4x Scope: `{sens['4x']}`\n"
        f"🎿 AWM Scope: `{sens['awm']}`\n"
        f"🌀 Gyroscope: `{sens['gyro']}`\n"
        f"🔫 Shoot Button Size: `{shoot_size}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Tip:* {TIPS[playstyle_key]}\n\n"
        f"Use /start to generate new settings."
    )

    keyboard = [[InlineKeyboardButton("🔄 Generate Again", callback_data="restart")]]
    await query.edit_message_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END


async def restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    saved_device = context.user_data.get("preferences", {}).get("device")
    saved_playstyle = context.user_data.get("preferences", {}).get("playstyle")
    context.user_data.pop("device", None)
    context.user_data.pop("playstyle", None)

    if saved_device and saved_playstyle:
        keyboard = [
            [InlineKeyboardButton(
                f"⚡ Use saved: {DEVICES[saved_device]} · {PLAYSTYLES[saved_playstyle]}",
                callback_data="use_saved"
            )],
            *[
                [InlineKeyboardButton(label, callback_data=f"device:{key}")]
                for key, label in DEVICES.items()
            ],
        ]
        text = (
            "🔥 *Free Fire Sensitivity Generator*\n\n"
            "Your saved preferences are shown above — tap to skip ahead to FPS, "
            "or pick a different device below.\n\n"
            "*Step 1 of 4* — Select your device:"
        )
    else:
        keyboard = [
            [InlineKeyboardButton(label, callback_data=f"device:{key}")]
            for key, label in DEVICES.items()
        ]
        text = (
            "🔥 *Free Fire Sensitivity Generator*\n\n"
            "Get custom sensitivity settings tuned to your device, playstyle, and FPS.\n\n"
            "*Step 1 of 4* — Select your device:"
        )

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return DEVICE


# ─── /tips ────────────────────────────────────────────────────────────────────

async def tips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"tips:{key}")]
        for key, label in PLAYSTYLES.items()
    ]
    await update.message.reply_text(
        "📖 *Free Fire Tips*\n\nChoose a playstyle to get a deep guide:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return TIPS_SELECT


async def tips_playstyle_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    playstyle_key = query.data.split(":")[1]
    text = DEEP_TIPS[playstyle_key] + "\n\n_Use /tips to read another guide._"

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"tips:{key}")]
        for key, label in PLAYSTYLES.items()
        if key != playstyle_key
    ]
    keyboard.append([InlineKeyboardButton("🎯 Generate Sensitivity", callback_data="go_start")])

    await query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )
    return TIPS_SELECT


async def tips_go_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    saved_device, saved_playstyle = get_saved(context)

    if saved_device and saved_playstyle:
        keyboard = [
            [InlineKeyboardButton(
                f"⚡ Use saved: {DEVICES[saved_device]} · {PLAYSTYLES[saved_playstyle]}",
                callback_data="use_saved"
            )],
            *[
                [InlineKeyboardButton(label, callback_data=f"device:{key}")]
                for key, label in DEVICES.items()
            ],
        ]
        text = (
            "🔥 *Free Fire Sensitivity Generator*\n\n"
            "Your saved preferences are shown above — tap to skip ahead to FPS, "
            "or pick a different device below.\n\n"
            "*Step 1 of 4* — Select your device:"
        )
    else:
        keyboard = [
            [InlineKeyboardButton(label, callback_data=f"device:{key}")]
            for key, label in DEVICES.items()
        ]
        text = (
            text = (
    "🔥 *Free Fire Sensitivity Generator*\n\n"
    "Get custom sensitivity settings tuned to your device, playstyle, and FPS.\n\n"
    "📱 You can tap a button or type your device name.\n"
    "Example: iPhone 12, Poco X5, Pixel 6a\n\n"
    "*Step 1 of 4* — Select your device:"
    
        )

    await query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )
    return DEVICE


# ─── /settings ────────────────────────────────────────────────────────────────

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    saved_device, saved_playstyle = get_saved(context)

    if saved_device and saved_playstyle:
        current = (
            f"⚙️ *Your Saved Preferences*\n\n"
            f"📱 Device: *{DEVICES[saved_device]}*\n"
            f"🎮 Playstyle: *{PLAYSTYLES[saved_playstyle]}*\n\n"
            "Update your device below, or /cancel to keep as-is."
        )
    else:
        current = (
            "⚙️ *Settings*\n\n"
            "No preferences saved yet. Pick your device and playstyle and they'll "
            "be remembered for future sessions.\n\n"
            "Select your device:"
        )

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"set_device:{key}")]
        for key, label in DEVICES.items()
    ]
    if saved_device and saved_playstyle:
        keyboard.append([InlineKeyboardButton("🗑 Clear saved preferences", callback_data="clear_prefs")])

    await update.message.reply_text(
        current, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )
    return SETTINGS_DEVICE


async def settings_device_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    device_key = query.data.split(":")[1]
    context.user_data["_settings_device"] = device_key

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"set_playstyle:{key}")]
        for key, label in PLAYSTYLES.items()
    ]
    text = (
        f"Device: *{DEVICES[device_key]}* ✅\n\n"
        "Now pick your default playstyle:"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return SETTINGS_PLAYSTYLE


async def settings_playstyle_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    playstyle_key = query.data.split(":")[1]
    device_key = context.user_data.pop("_settings_device")

    context.user_data.setdefault("preferences", {})
    context.user_data["preferences"]["device"] = device_key
    context.user_data["preferences"]["playstyle"] = playstyle_key

    text = (
        f"✅ *Preferences saved!*\n\n"
        f"📱 Device: *{DEVICES[device_key]}*\n"
        f"🎮 Playstyle: *{PLAYSTYLES[playstyle_key]}*\n\n"
        "Next time you use /start, you'll see a shortcut button to skip straight to FPS."
    )
    await query.edit_message_text(text, parse_mode="Markdown")
    return ConversationHandler.END


async def clear_prefs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("preferences", None)
    await query.edit_message_text("🗑 Preferences cleared. Use /settings to set new ones.")
    return ConversationHandler.END


# ─── /cancel & main ───────────────────────────────────────────────────────────

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    s = context.user_data.get("stats", {})
    total = s.get("total", 0)

    if total == 0:
        await update.message.reply_text(
            "📊 *Your Stats*\n\nNo sensitivity settings generated yet. Use /start to get your first one!",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    playstyles = s.get("playstyles", {})
    devices = s.get("devices", {})
    fps_counts = s.get("fps", {})

    top_playstyle = max(playstyles, key=playstyles.get)
    top_device = max(devices, key=devices.get)
    top_fps = max(fps_counts, key=fps_counts.get)

    playstyle_lines = "\n".join(
        f"  {PLAYSTYLES[k]}: `{v}x`"
        for k, v in sorted(playstyles.items(), key=lambda x: -x[1])
    )
    device_lines = "\n".join(
        f"  {DEVICES[k]}: `{v}x`"
        for k, v in sorted(devices.items(), key=lambda x: -x[1])
    )
    fps_lines = "\n".join(
        f"  {FPS_OPTIONS[k]}: `{v}x`"
        for k, v in sorted(fps_counts.items(), key=lambda x: -x[1])
    )

    text = (
        f"📊 *Your Free Fire Bot Stats*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Total generated: `{total}`\n\n"
        f"🏆 *Favourites*\n"
        f"  Playstyle: {PLAYSTYLES[top_playstyle]}\n"
        f"  Device: {DEVICES[top_device]}\n"
        f"  FPS: {FPS_OPTIONS[top_fps]}\n\n"
        f"🎮 *By Playstyle*\n{playstyle_lines}\n\n"
        f"📱 *By Device*\n{device_lines}\n\n"
        f"⚡ *By FPS*\n{fps_lines}"
    )

    keyboard = [[InlineKeyboardButton("🎯 Generate New Settings", callback_data="go_start")]]
    await update.message.reply_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )
    return TIPS_SELECT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelled. Use /start to generate settings or /settings to update preferences.")
    return ConversationHandler.END


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("settings", settings),
            CommandHandler("tips", tips),
            CommandHandler("stats", stats),
        ],
        states={
                DEVICE: [
    MessageHandler(filters.TEXT & ~filters.COMMAND, device_text),
    CallbackQueryHandler(use_saved, pattern=r"^use_saved$"),
    CallbackQueryHandler(device_selected, pattern=r"^device:"),
    CallbackQueryHandler(restart_callback, pattern=r"^restart$"),
            
    ],
            PLAYSTYLE: [
                CallbackQueryHandler(playstyle_selected, pattern=r"^playstyle:"),
            ],
            FPS: [
                CallbackQueryHandler(fps_selected, pattern=r"^fps:"),
            ],
            GRAPHICS: [
                CallbackQueryHandler(graphics_selected, pattern=r"^graphics:"),
            ],
            SETTINGS_DEVICE: [
                CallbackQueryHandler(settings_device_selected, pattern=r"^set_device:"),
                CallbackQueryHandler(clear_prefs, pattern=r"^clear_prefs$"),
            ],
            SETTINGS_PLAYSTYLE: [
                CallbackQueryHandler(settings_playstyle_selected, pattern=r"^set_playstyle:"),
            ],
            TIPS_SELECT: [
                CallbackQueryHandler(tips_playstyle_selected, pattern=r"^tips:"),
                CallbackQueryHandler(tips_go_start, pattern=r"^go_start$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
        per_chat=True,
        per_user=True,
    )

    app.add_handler(conv_handler)

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

