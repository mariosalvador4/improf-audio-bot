import os
from io import BytesIO

import discord
from discord.ext import commands
from elevenlabs import ElevenLabs

# =========================
#  VARIABLES DE ENTORNO
# =========================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --- MARIO (tu cuenta de ElevenLabs) ---
ELEVEN_API_KEY_MARIO = os.getenv("ELEVEN_API_KEY")
VOICE_ID_MARIO = os.getenv("VOICE_ID_MARIO")
CHANNEL_ID_MARIO = int(os.getenv("CHANNEL_ID_MARIO", "0"))

# --- ROMI (cuenta de Romiflexy) ---
ELEVEN_API_KEY_ROMI = os.getenv("ELEVEN_API_KEY_ROMI")
VOICE_ID_ROMI = os.getenv("VOICE_ID_ROMI")
CHANNEL_ID_ROMI = int(os.getenv("CHANNEL_ID_ROMI", "0"))

# Validación
if not DISCORD_TOKEN:
    raise RuntimeError("Falta DISCORD_TOKEN")

if not ELEVEN_API_KEY_MARIO:
    raise RuntimeError("Falta ELEVEN_API_KEY (MARIO)")
if not VOICE_ID_MARIO:
    raise RuntimeError("Falta VOICE_ID_MARIO")
if CHANNEL_ID_MARIO == 0:
    raise RuntimeError("Falta CHANNEL_ID_MARIO")

if not ELEVEN_API_KEY_ROMI:
    raise RuntimeError("Falta ELEVEN_API_KEY_ROMI")
if not VOICE_ID_ROMI:
    raise RuntimeError("Falta VOICE_ID_ROMI")
if CHANNEL_ID_ROMI == 0:
    raise RuntimeError("Falta CHANNEL_ID_ROMI")

# =========================
#  CLIENTES ELEVENLABS
# =========================

client_mario = ElevenLabs(api_key=ELEVEN_API_KEY_MARIO)
client_romi = ElevenLabs(api_key=ELEVEN_API_KEY_ROMI)

# Mapeo: canal → (nombre modelo, cliente, voice_id)
CHANNEL_TO_SETTINGS = {
    CHANNEL_ID_MARIO: ("Mario", client_mario, VOICE_ID_MARIO),
    CHANNEL_ID_ROMI: ("Romi", client_romi, VOICE_ID_ROMI),
}

# =========================
#  CONFIG DISCORD
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
    if channel_id not in CHANNEL_TO_SETTINGS:
        return

    text = message.content.strip()
    if not text:
        return

    model_name, client, voice_id = CHANNEL_TO_SETTINGS[channel_id]

    print(f"📩 Mensaje recibido ({model_name}): {text}")

    try:
        await message.channel.send(f"🎙 Generando audio con la voz de {model_name}...")

        audio_stream = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            text=text,
            output_format="mp3_44100_128",
            voice_settings={
                "stability": 0.60,
                "similarity_boost": 0.90,
                "style": 0.35,
                "use_speaker_boost": True,
            },
        )

        audio_bytes = b"".join(audio_stream)
        filename = f"{model_name.lower()}_audio.mp3"

        audio_file = discord.File(BytesIO(audio_bytes), filename=filename)

        await message.channel.send(file=audio_file)
        print(f"✅ Audio enviado correctamente ({model_name})")

    except Exception as e:
        print(f"❌ Error generando audio ({model_name}): {e}")
        await message.channel.send("❌ Error generando el audio. Avísale a Mario.")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
