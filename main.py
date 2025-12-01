import os
from io import BytesIO

import discord
from discord.ext import commands
from elevenlabs import ElevenLabs

# =========================
#   VARIABLES DE ENTORNO
# =========================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Mario (tu cuenta)
ELEVEN_API_KEY_MARIO = os.getenv("ELEVEN_API_KEY")
VOICE_ID_MARIO = os.getenv("VOICE_ID_MARIO")
CHANNEL_ID_MARIO = int(os.getenv("CHANNEL_ID_MARIO", "0"))

# Romi (su cuenta)
ELEVEN_API_KEY_ROMI = os.getenv("ELEVEN_API_KEY_ROMI")
VOICE_ID_ROMI = os.getenv("VOICE_ID_ROMI")
CHANNEL_ID_ROMI = int(os.getenv("CHANNEL_ID_ROMI", "0"))

# Validaciones
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

# =========================
#   CLIENTES ELEVEN LABS
# =========================

client_mario = ElevenLabs(api_key=ELEVEN_API_KEY_MARIO)
client_romi = ElevenLabs(api_key=ELEVEN_API_KEY_ROMI)

# Canal → (nombre, voice_id, cliente)
CHANNEL_TO_DATA = {
    CHANNEL_ID_MARIO: ("Mario", VOICE_ID_MARIO, client_mario),
    CHANNEL_ID_ROMI: ("Romi", VOICE_ID_ROMI, client_romi),
}

# =========================
#   CONFIG DISCORD
# =========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"🔥 Bot conectado como {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("Generando audios IMPROF 🎧"),
    )


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    channel_id = message.channel.id

    if channel_id not in CHANNEL_TO_DATA:
        return

    text = message.content.strip()
    if not text:
        return

    model_name, voice_id, eleven_client = CHANNEL_TO_DATA[channel_id]

    print(f"📩 Mensaje en canal {channel_id} ({model_name}): {text}")

    try:
        await message.channel.send(f"🎙 Generando audio con la voz de **{model_name}**...")

        # =========================
        #  CONFIGURACIÓN EXACTA QUE PEDISTE
        # =========================
        audio_stream = eleven_client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            text=text,
            output_format="mp3_44100_128",
            voice_settings={
                "stability": 0.35,
                "similarity_boost": 0.60,
                "style": 0.20,
                "use_speaker_boost": True,
            },
            voice_speed=0.90,  # VELOCIDAD EXACTA
        )

        audio_bytes = b"".join(audio_stream)
        filename = f"{model_name.lower()}_audio.mp3"

        audio_file = discord.File(BytesIO(audio_bytes), filename=filename)

        await message.channel.send(file=audio_file)
        print(f"✅ Audio enviado correctamente ({model_name})")

    except Exception as e:
        print(f"❌ Error generando audio para {model_name}: {e}")
        await message.channel.send(
            "❌ Ha habido un error generando el audio. Avísale a Mario."
        )

    await bot.process_commands(message)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
