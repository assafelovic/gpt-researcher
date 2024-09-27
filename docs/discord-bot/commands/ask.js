const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('ask')
        .setDescription('Ask a question to the bot'),
    async execute(interaction) {
        await interaction.reply('Please provide your question.');
    }
};
