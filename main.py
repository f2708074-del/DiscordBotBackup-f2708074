import discord
from discord.ext import commands
import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

class SilentBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
    
    async def setup_hook(self):
        for filename in os.listdir('./commands'):
            if filename.endswith('.py') and filename != '__init__.py':
                await self.load_extension(f'commands.{filename[:-3]}')
        await self.tree.sync()

bot = SilentBot()

async def web_server():
    app = web.Application()
    app.router.add_get('/', lambda request: web.Response(text="Bot is running!"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    await site.start()

@bot.event
async def on_ready():
    """
    ===================================================
    PERSONALIZACIÓN DEL ESTADO DEL BOT
    ===================================================
    
    CONFIGURACIÓN MEDIANTE VARIABLES DE ENTORNO (.env):
    
    1. ACTIVITY_TYPE: Tipo de actividad
       - playing: Jugando a... (valor por defecto)
       - watching: Viendo...
       - listening: Escuchando...
       - streaming: Transmitiendo...
       - competing: Compitiendo en...
       - none: Sin actividad (el bot no mostrará nada)
    
    2. ACTIVITY_NAME: Texto que se mostrará
       - Ejemplos: "tu servidor", "música", "!comandos"
       - Si ACTIVITY_TYPE es "none", este valor se ignora
    
    3. STATUS: Estado de disponibilidad
       - online: En línea (verde)
       - idle: Ausente (amarillo)
       - dnd: No molestar (rojo)
       - offline: Invisible (pero funcional)
       - invisible: Equivalente a offline
    
    EJEMPLOS DE CONFIGURACIÓN:
    
      Bot moderador:
        ACTIVITY_TYPE=watching
        ACTIVITY_NAME=el servidor
        STATUS=online
    
      Bot musical:
        ACTIVITY_TYPE=listening
        ACTIVITY_NAME=música
        STATUS=online
    
      Bot sin actividad:
        ACTIVITY_TYPE=none
        STATUS=online
    
    NOTAS:
      - Los cambios se aplican al reiniciar el bot
      - El estado 'invisible' oculta el bot pero sigue funcionando
      - Modifica estas variables en el archivo .env
    ===================================================
    """
    
    # ==============================================
    # CONFIGURACIÓN DEL ESTADO - EDITA ESTAS VARIABLES
    # ==============================================
    status_type = os.getenv('STATUS', 'online').lower()
    activity_type = os.getenv('ACTIVITY_TYPE', 'none').lower()
    activity_name = os.getenv('ACTIVITY_NAME', 'Default Activity')
    # ==============================================

    # Mapear tipos de actividad
    activity_dict = {
        'playing': discord.ActivityType.playing,
        'streaming': discord.ActivityType.streaming,
        'listening': discord.ActivityType.listening,
        'watching': discord.ActivityType.watching,
        'competing': discord.ActivityType.competing,
        'none': None  # Nueva opción para sin actividad
    }

    # Mapear estados
    status_dict = {
        'online': discord.Status.online,
        'dnd': discord.Status.dnd,
        'idle': discord.Status.idle,
        'offline': discord.Status.offline,
        'invisible': discord.Status.invisible
    }

    # Configurar actividad (o ninguna)
    if activity_type == 'none':
        activity = None  # Sin actividad
    else:
        activity = discord.Activity(
            type=activity_dict.get(activity_type, discord.ActivityType.playing),
            name=activity_name
        )

    # Establecer el estado personalizado
    await bot.change_presence(
        activity=activity,
        status=status_dict.get(status_type, discord.Status.online)
    )

    # Iniciar el servidor web
    asyncio.create_task(web_server())

token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    exit("Token no encontrado")
