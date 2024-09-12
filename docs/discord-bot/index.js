require('dotenv').config();
const { Client, GatewayIntentBits, ActionRowBuilder, Events, ModalBuilder, TextInputBuilder, TextInputStyle, ChannelType } = require('discord.js');
const keepAlive = require('./server');
const { sendWebhookMessage } = require('./gptr-webhook');
const e = require('express');
const { jsonrepair } = require('jsonrepair')

// Define the intents your bot needs
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.DirectMessages
  ],
});

function splitMessage(message, chunkSize = 1500) {
  const chunks = [];
  for (let i = 0; i < message.length; i += chunkSize) {
    chunks.push(message.slice(i, i + chunkSize));
  }
  return chunks;
}

client.on('ready', () => {
  console.log(`Logged in as ${client.user.tag}!`);
});

client.on('messageCreate', async message => {
  if (message.author.bot) return;
  await message.reply('please use the /ask command to launch a report');
});

client.on(Events.InteractionCreate, async interaction => {
  if (!interaction.isChatInputCommand()) return;

  if (interaction.commandName === 'ask') {
    // Create the modal
    const modal = new ModalBuilder()
      .setCustomId('myModal')
      .setTitle('Ask the AI Dev Team');

    // Add components to modal
    const queryInput = new TextInputBuilder()
      .setCustomId('queryInput')
      .setLabel('Your question')
      .setStyle(TextInputStyle.Paragraph)
      .setPlaceholder('What are you exploring / trying to code today?');

    const relevantFileNamesInput = new TextInputBuilder()
      .setCustomId('relevantFileNamesInput')
      .setLabel('Relevant file names (optional)')
      .setStyle(TextInputStyle.Paragraph)
      .setPlaceholder('Where would you like us to look / how would you like this implemented?')
      .setRequired(false);

    const repoNameInput = new TextInputBuilder()
      .setCustomId('repoNameInput')
      .setLabel('Repo name (optional)')
      .setStyle(TextInputStyle.Short)
      .setPlaceholder('assafelovic/gpt-researcher')
      .setRequired(false);

    const branchNameInput = new TextInputBuilder()
      .setCustomId('branchNameInput')
      .setLabel('Branch name (optional)')
      .setStyle(TextInputStyle.Short)
      .setPlaceholder('master')
      .setRequired(false);

    // so you need one action row per text input.
    const firstActionRow = new ActionRowBuilder().addComponents(queryInput);
    const secondActionRow = new ActionRowBuilder().addComponents(relevantFileNamesInput);
    const thirdActionRow = new ActionRowBuilder().addComponents(repoNameInput);
    const fourthActionRow = new ActionRowBuilder().addComponents(branchNameInput);

    // Add inputs to the modal
    modal.addComponents(firstActionRow, secondActionRow, thirdActionRow, fourthActionRow);

    // Show the modal to the user
    await interaction.showModal(modal);
  }
});

client.on(Events.InteractionCreate, async interaction => {
  if (!interaction.isModalSubmit()) return;
  if (interaction.customId === 'myModal') {
    const query = interaction.fields.getTextInputValue('queryInput');
    const relevantFileNames = interaction.fields.getTextInputValue('relevantFileNamesInput');
    const repoName = interaction.fields.getTextInputValue('repoNameInput');
    const branchName = interaction.fields.getTextInputValue('branchNameInput');

    if (interaction?.channel?.type === ChannelType.GuildText) {
      const thread = await interaction.channel.threads.create({
        name: `Discussion: ${query.slice(0, 30)}...`,
        autoArchiveDuration: 60,
        reason: 'Discussion thread for the query',
      });
      await runDevTeam({ interaction, query, relevantFileNames, repoName, branchName, thread });
    } else {
      await runDevTeam({ interaction, query, relevantFileNames, repoName, branchName });
    }
  }
});

async function runDevTeam({ interaction, query, relevantFileNames, repoName, branchName, thread }) {
  const queryToDisplay = `**user query**: ${query}. 
                          ${relevantFileNames ? '\n**relevant file names**: ' + relevantFileNames : ''} 
                          ${repoName ? '\n**repo name**: ' + repoName : ''}
                          ${branchName ? '\n**branch name**: ' + branchName : ''}
                          \nLooking through the code to investigate your query... give me a minute or so`

  if(!thread){
    await interaction.reply({ content: queryToDisplay});
  } else {
    await thread.send(queryToDisplay);
  }

  try {
    // Await the response from GPTR via WebSocket
    let gptrResponse = await sendWebhookMessage({query, relevantFileNames, repoName, branchName});

    // Check if the response is valid
    if (gptrResponse && gptrResponse.rubber_ducker_thoughts) {
      // Combine and split the messages into chunks
      const rubberDuckerChunks = splitMessage(JSON.parse(jsonrepair(gptrResponse.rubber_ducker_thoughts)).thoughts);

      // Send each chunk of Rubber Ducker Thoughts
      for (const chunk of rubberDuckerChunks) {
        if(!thread){
          await interaction.followUp({ content: chunk });
        } else {
          await thread.send(chunk);
        }
      }

      return true;
    } else {
      if(!thread){
        return await interaction.followUp({ content: 'Invalid response received from GPTR.' });
      } else {
        return await thread.send('Invalid response received from GPTR.');
      }
    }
  } catch (error) {
    console.error({ content: 'Error handling message:', error });
    if(!thread){
        return await interaction.followUp({ content: 'There was an error processing your request.'})
    } else {
        return await thread.send('There was an error processing your request.');
    }
  }
}

keepAlive();
client.login(process.env.DISCORD_BOT_TOKEN);