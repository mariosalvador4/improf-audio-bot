import os
from io import BytesIO

import discord
from discord.ext import commands
from elevenlabs import ElevenLabs

# =========================
#  VARIABLES DE ENTORNO
# =========================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

VOICE_ID_MARIO = os.getenv("VOICE_ID_MARIO")
VOICE_ID_ANDREA = os.getenv("VOICE_ID_ANDREA")

CHANNEL_ID_MARIO = int(os.getenv("CHANNEL_ID_MARIO", "0"))
CHANNEL_ID_ANDREA = int(os.getenv("CHANNEL_ID_ANDREA", "0"))

if not DISCORD_TOKEN:
    raise RuntimeError("Falta DISCORD_TOKEN en Railway")
if not ELEVEN_API_KEY:
    raise RuntimeError("Falta ELEVEN_API_KEY en Railway")
if not VOICE_ID_MARIO:
    raise RuntimeError("Falta VOICE_ID_MARIO en Railway")
if not VOICE_ID_ANDREA:
    raise RuntimeError("Falta VOICE_ID_ANDREA en Railway")
if CHANNEL_ID_MARIO == 0:
    raise RuntimeError("Falta CHANNEL_ID_MARIO en Railway")
if CHANNEL_ID_ANDREA == 0:
    raise RuntimeError("Falta CHANNEL_ID_ANDREA en Railway")

# Cliente único de ElevenLabs (misma cuenta para ambas voces)
eleven_client = ElevenLabs(api_key=ELEVEN_API_KEY)

# Mapear canal -> voz y nombre (solo para logs/mensajes)
CHANNEL_TO_VOICE = {
    CHANNEL_ID_MARIO: ("Mario", VOICE_ID_MARIO),
    CHANNEL_ID_ANDREA: ("Andrea", VOICE_ID_ANDREA),
}

# =========================
#  CONFIG DISCORD
# =========================
intents = discord.Intents.default()
intents.message_content = True  # NECESARIO para leer mensajes

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
    # Ignorar mensajes del propio bot
    if message.author.bot:
        return

    channel_id = message.channel.id

    # Solo reaccionar en los canales configurados (Mario / Andrea)
    if channel_id not in CHANNEL_TO_VOICE:
        return

    text = message.content.strip()
    if not text:
        return

    model_name, voice_id = CHANNEL_TO_VOICE[channel_id]

    print(f"📩 Mensaje recibido en canal {channel_id} ({model_name}): {text}")

    try:
        # Aviso de que está generando el audio
        await message.channel.send(f"🎙 Generando audio con la voz de {model_name}...")

        # Llamada a ElevenLabs con modelo profesional y ajustes de voz
        audio_stream = eleven_client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",  # modelo PRO, misma calidad que en la web
            text=text,
            output_format="mp3_44100_128",
            voice_settings={
                "stability": 0.60,
                "similarity_boost": 0.90,
                "style": 0.35,
                "use_speaker_boost": True,
            },
        )

        # audio_stream es un generador de bytes -> lo juntamos
        audio_bytes = b"".join(audio_stream)
        filename = f"{model_name.lower()}_audio.mp3"

        audio_file = discord.File(
            BytesIO(audio_bytes),
            filename=filename,
        )

        await message.channel.send(file=audio_file)
        print(f"✅ Audio enviado correctamente ({model_name})")

    except Exception as e:
        print(f"❌ Error generando audio para {model_name}: {e}")
        await message.channel.send(
            f"❌ Ha habido un error generando el audio. Avísale a Mario."
        )

    # Para que sigan funcionando comandos si algún día los usas
    await bot.process_commands(message)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
