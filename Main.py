import os
import io
import asyncio
import discord
from discord.ext import commands
from elevenlabs import ElevenLabs

# --- CONFIG DESDE VARIABLES DE ENTORNO ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
VOICE_ID = os.getenv("VOICE_ID_MARIO")
CHANNEL_ID = int(os.getenv("CHANNEL_ID_MARIO", "0"))

if not all([DISCORD_TOKEN, ELEVEN_API_KEY, VOICE_ID, CHANNEL_ID]):
    raise RuntimeError("Faltan variables de entorno obligatorias.")

# Cliente ElevenLabs
client_eleven = ElevenLabs(api_key=ELEVEN_API_KEY)

# Intents de Discord para leer mensajes
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"🔥 Bot conectado como {bot.user}")


async def generar_audio(texto: str) -> io.BytesIO:
    """
    Envía texto a ElevenLabs -> devuelve MP3.
    """
    audio = client_eleven.generate(
        text=texto,
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128"
    )

    data = b"".join(audio)
    buffer = io.BytesIO(data)
    buffer.seek(0)
    return buffer


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id == CHANNEL_ID:
        texto = message.content.strip()
        if not texto:
            return

        aviso = await message.channel.send("🎙 Generando audio con la voz de Mario…")

        try:
            audio_buffer = await asyncio.to_thread(generar_audio, texto)
            file = discord.File(fp=audio_buffer, filename="mario_audio.mp3")

            await message.channel.send(
                content=f"✅ Aquí tienes el audio:",
                file=file,
                reference=message
            )

        except Exception as e:
            print("ERROR:", e)
            await message.channel.send("❌ Error generando el audio. Revisa la API.")

        finally:
            await aviso.delete()

    await bot.process_commands(message)


bot.run(DISCORD_TOKEN)
