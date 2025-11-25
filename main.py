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
VOICE_ID = os.getenv("VOICE_ID_MARIO")
CHANNEL_ID = int(os.getenv("CHANNEL_ID_MARIO", "0"))

if not DISCORD_TOKEN:
    raise RuntimeError("Falta DISCORD_TOKEN en Railway")
if not ELEVEN_API_KEY:
    raise RuntimeError("Falta ELEVEN_API_KEY en Railway")
if not VOICE_ID:
    raise RuntimeError("Falta VOICE_ID_MARIO en Railway")
if CHANNEL_ID == 0:
    raise RuntimeError("Falta CHANNEL_ID_MARIO en Railway")

# Cliente ElevenLabs
eleven_client = ElevenLabs(api_key=ELEVEN_API_KEY)

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
        activity=discord.Game("Generando audios de Mario 🎧"),
    )


@bot.event
async def on_message(message: discord.Message):
    # Ignorar mensajes del propio bot
    if message.author.bot:
        return

    # Solo reaccionar en el canal de audios configurado
    if message.channel.id != CHANNEL_ID:
        return

    text = message.content.strip()
    if not text:
        return

    print(f"📩 Mensaje recibido en canal audios-mario: {text}")

    try:
        # Aviso de que está generando el audio
        await message.channel.send("🎙 Generando audio con la voz de Mario...")

        # Llamada a ElevenLabs con modelo profesional y ajustes de voz
        audio_stream = eleven_client.text_to_speech.convert(
            voice_id=VOICE_ID,
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
        audio_file = discord.File(
            BytesIO(audio_bytes),
            filename="mario_audio.mp3",
        )

        await message.channel.send(file=audio_file)
        print("✅ Audio enviado correctamente")

    except Exception as e:
        print(f"❌ Error generando audio: {e}")
        await message.channel.send(
            "❌ Ha habido un error generando el audio. Avísale a Mario."
        )

    # Para que sigan funcionando comandos si algún día los usas
    await bot.process_commands(message)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
