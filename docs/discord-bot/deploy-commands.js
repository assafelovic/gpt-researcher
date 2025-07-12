const { Client, GatewayIntentBits, REST, Routes } = require('discord.js');
require('dotenv').config();

// Create a new REST client and set your bot token
const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_BOT_TOKEN);

// Define commands
const commands = [
    {
        name: 'ping',
        description: 'Replies with Pong!',
    },
    {
        name: 'ask',
        description: 'Ask a question to the bot',
    },
];

// Deploy commands to Discord
(async () => {
    try {
        console.log('Started refreshing application (/) commands.');

        await rest.put(Routes.applicationCommands(process.env.DISCORD_CLIENT_ID), {
            body: commands,
        });

        console.log('Successfully reloaded application (/) commands.');
    } catch (error) {
        console.error(error);
    }
})();
