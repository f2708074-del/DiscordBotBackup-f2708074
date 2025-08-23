import discord
from discord.ext import commands
import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import glob

# Función para obtener la clave de encriptación
def get_encryption_key():
    """Obtiene y deriva la clave desde la variable de entorno KEY_CODE"""
    try:
        key_code = os.environ.get('KEY_CODE')
        if not key_code:
            raise ValueError("KEY_CODE no está definida en las variables de entorno")
        
        # Decodifica la clave base64
        key = base64.urlsafe_b64decode(key_code)
        
        # Aseguramos que tenga exactamente 32 bytes
        if len(key) != 32:
            # Si no es exactamente 32 bytes, derivamos una clave usando PBKDF2
            salt = b'fixed_salt_for_github'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(key_code.encode())
        
        return key
    except Exception as e:
        raise

# Función para desencriptar archivos
def decrypt_file(encrypted_content, key):
    """Descifra contenido usando AES-256 en modo CBC"""
    try:
        # Decodifica de Base64 a bytes
        encrypted_data = base64.b64decode(encrypted_content)
        
        # Separa el IV y el ciphertext
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Configura el descifrador
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Descifra el contenido
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Elimina el padding
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext.decode('utf-8')
    except Exception:
        # Si falla, asumimos que no está encriptado
        return None

# Función para verificar y desencriptar scripts
def decrypt_scripts():
    """Verifica y desencripta todos los scripts en el repositorio"""
    try:
        key = get_encryption_key()
        # Buscar archivos .encrypted.py (encriptados)
        encrypted_files = glob.glob("**/*.encrypted.py", recursive=True)
        
        for encrypted_file_path in encrypted_files:
            with open(encrypted_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Intentar desencriptar
            decrypted_content = decrypt_file(content, key)
            
            # Si la desencriptación fue exitosa, escribir el archivo .py
            if decrypted_content is not None:
                # Crear nombre de archivo .py (remplazando .encrypted.py por .py)
                py_file_path = encrypted_file_path.replace('.encrypted.py', '.py')
                with open(py_file_path, 'w', encoding='utf-8') as file:
                    file.write(decrypted_content)
                
    except Exception:
        # Silenciar errores
        pass

# Ejecutar desencriptación antes de continuar
decrypt_scripts()

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
    status_type = os.getenv('STATUS', 'online').lower()
    activity_type = os.getenv('ACTIVITY_TYPE', 'none').lower()
    activity_name = os.getenv('ACTIVITY_NAME', 'Default Activity')

    activity_dict = {
        'playing': discord.ActivityType.playing,
        'streaming': discord.ActivityType.streaming,
        'listening': discord.ActivityType.listening,
        'watching': discord.ActivityType.watching,
        'competing': discord.ActivityType.competing,
        'none': None
    }

    status_dict = {
        'online': discord.Status.online,
        'dnd': discord.Status.dnd,
        'idle': discord.Status.idle,
        'offline': discord.Status.offline,
        'invisible': discord.Status.invisible
    }

    if activity_type == 'none':
        activity = None
    else:
        activity = discord.Activity(
            type=activity_dict.get(activity_type, discord.ActivityType.playing),
            name=activity_name
        )

    await bot.change_presence(
        activity=activity,
        status=status_dict.get(status_type, discord.Status.online)
    )

    asyncio.create_task(web_server())

token = os.getenv('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    exit("Token no encontrado")
