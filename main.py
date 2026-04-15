import os
import re
from io import BytesIO

import discord
from discord.ext import commands
from elevenlabs import ElevenLabs

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

ELEVEN_API_KEY_MARIO = os.getenv("ELEVEN_API_KEY")
VOICE_ID_MARIO = os.getenv("VOICE_ID_MARIO")
CHANNEL_ID_MARIO = int(os.getenv("CHANNEL_ID_MARIO", "0"))

ELEVEN_API_KEY_ROMI = os.getenv("ELEVEN_API_KEY_ROMI")
VOICE_ID_ROMI = os.getenv("VOICE_ID_ROMI")
CHANNEL_ID_ROMI = int(os.getenv("CHANNEL_ID_ROMI", "0"))

ELEVEN_MODEL_ID_DEFAULT = os.getenv("ELEVEN_MODEL_ID_DEFAULT", "eleven_multilingual_v2")
ELEVEN_MODEL_ID_EXPRESSIVE = os.getenv("ELEVEN_MODEL_ID_EXPRESSIVE", "eleven_v3")

required_vars = {
    "DISCORD_TOKEN": DISCORD_TOKEN,
    "ELEVEN_API_KEY_MARIO": ELEVEN_API_KEY_MARIO,
    "VOICE_ID_MARIO": VOICE_ID_MARIO,
    "CHANNEL_ID_MARIO": CHANNEL_ID_MARIO,
    "ELEVEN_API_KEY_ROMI": ELEVEN_API_KEY_ROMI,
    "VOICE_ID_ROMI": VOICE_ID_ROMI,
    "CHANNEL_ID_ROMI": CHANNEL_ID_ROMI,
}

for name, value in required_vars.items():
    if not value or value == 0:
        raise RuntimeError(f"❌ Falta la variable de entorno: {name}")

client_mario = ElevenLabs(api_key=ELEVEN_API_KEY_MARIO)
client_romi = ElevenLabs(api_key=ELEVEN_API_KEY_ROMI)

CHANNEL_TO_DATA = {
    CHANNEL_ID_MARIO: ("Mario", VOICE_ID_MARIO, client_mario),
    CHANNEL_ID_ROMI: ("Romi", VOICE_ID_ROMI, client_romi),
}

print("✅ Bot configurado con Mario y Romi")
print(f"📌 CHANNEL_ID_MARIO cargado: {CHANNEL_ID_MARIO}")
print(f"📌 CHANNEL_ID_ROMI cargado: {CHANNEL_ID_ROMI}")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

def normalize_prompt_text(text: str) -> str:
    replacements = {
        r"\(susurro\)": "[whispers]",
        r"\(susurrando\)": "[whispers]",
        r"\(lento\)": "[slow]",
        r"\(despacio\)": "[slow]",
        r"\(emocionado\)": "[excited]",
        r"\(excitado\)": "[excited]",
        r"\(riendo\)": "[laughs]",
        r"\(risa\)": "[laughs]",
        r"\(suspiro\)": "[sighs]",
        r"\(pausa\)": "[pause]",
        r"\(gemido\)": "[moans]",
        r"\(gimiendo\)": "[moans]",
        r"\(enfadado\)": "[excited]",
        r"\(enamorado\)": "[slow][whispers]",
    }

    normalized = text
    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    return normalized.strip()

def should_use_expressive_model(text: str) -> bool:
    has_inline_tags = bool(re.search(r"\[[^\[\]]+\]", text))
    has_aliases = bool(
        re.search(
            r"\((susurro|susurrando|lento|despacio|emocionado|excitado|riendo|risa|suspiro|pausa|gemido|gimiendo|enfadado|enamorado)\)",
            text,
            flags=re.IGNORECASE
        )
    )
    return has_inline_tags or has_aliases

def get_model_id_for_text(text: str) -> str:
    return ELEVEN_MODEL_ID_EXPRESSIVE if should_use_expressive_model(text) else ELEVEN_MODEL_ID_DEFAULT

@bot.event
async def on_ready():
    print(f"🔥 Bot conectado como {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("Generando audios IMPROF 🎧"),
    )

@bot.event
async def on_message(message: discord.Message):
    print(f"🟡 Mensaje detectado en canal {message.channel.id} de {message.author}")

    if message.author.bot:
        print("↪ Ignorado porque es de un bot")
        return

    channel_id = message.channel.id

    if channel_id not in CHANNEL_TO_DATA:
        print(f"⚪ Canal no configurado: {channel_id}")
        return

    raw_text = message.content.strip()
    if not raw_text:
        print("⚪ Mensaje vacío")
        return

    model_name, voice_id, eleven_client = CHANNEL_TO_DATA[channel_id]
    model_id = get_model_id_for_text(raw_text)
    text = normalize_prompt_text(raw_text)

    print(f"📩 Procesando mensaje para {model_name}")
    print(f"   Texto original: {raw_text}")
    print(f"   Texto final: {text}")
    print(f"   Modelo: {model_id}")

    try:
        await message.channel.send(f"🎙 Generando audio con la voz de **{model_name}**...")

        audio_stream = eleven_client.text_to_speech.convert(
            voice_id=voice_id,
            model_id=model_id,
            text=text,
            output_format="mp3_44100_128",
            voice_settings={
                "stability": 0.35,
                "similarity_boost": 0.60,
                "style": 0.20,
                "use_speaker_boost": True,
            },
        )

        audio_bytes = b"".join(audio_stream)
        filename = f"{model_name.lower()}_audio.mp3"
        audio_file = discord.File(BytesIO(audio_bytes), filename=filename)

        await message.channel.send(file=audio_file)
        print(f"✅ Audio enviado correctamente ({model_name})")

    except Exception as e:
        print(f"❌ Error generando audio para {model_name}: {e}")
        await message.channel.send("❌ Error generando el audio.")

    await bot.process_commands(message)

if __name__ == "__main__":
    print("🚀 Iniciando bot...")
    bot.run(DISCORD_TOKEN)