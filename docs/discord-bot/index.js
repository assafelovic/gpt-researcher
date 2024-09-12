require('dotenv').config();
const { Client, GatewayIntentBits, ActionRowBuilder, Events, ModalBuilder, TextInputBuilder, TextInputStyle, ChannelType } = require('discord.js');
const keepAlive = require('./server');
const { sendWebhookMessage } = require('./gptr-webhook');
const { jsonrepair } = require('jsonrepair');

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
  if (interaction.isChatInputCommand()) {
    if (interaction.commandName === 'ask') {
      const modal = new ModalBuilder()
        .setCustomId('myModal')
        .setTitle('Ask the AI Dev Team');

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

      const firstActionRow = new ActionRowBuilder().addComponents(queryInput);
      const secondActionRow = new ActionRowBuilder().addComponents(relevantFileNamesInput);
      const thirdActionRow = new ActionRowBuilder().addComponents(repoNameInput);
      const fourthActionRow = new ActionRowBuilder().addComponents(branchNameInput);

      modal.addComponents(firstActionRow, secondActionRow, thirdActionRow, fourthActionRow);

      await interaction.showModal(modal);
    }
  } else if (interaction.isModalSubmit()) {
    if (interaction.customId === 'myModal') {
      const query = interaction.fields.getTextInputValue('queryInput');
      const relevantFileNames = interaction.fields.getTextInputValue('relevantFileNamesInput');
      const repoName = interaction.fields.getTextInputValue('repoNameInput');
      const branchName = interaction.fields.getTextInputValue('branchNameInput');

      let thread;
      if (interaction?.channel?.type === ChannelType.GuildText) {
        thread = await interaction.channel.threads.create({
          name: `Discussion: ${query.slice(0, 30)}...`,
          autoArchiveDuration: 60,
          reason: 'Discussion thread for the query',
        });
      }

      await interaction.deferUpdate();

      runDevTeam({ interaction, query, relevantFileNames, repoName, branchName, thread })
        .catch(console.error);
    }
  }
});

async function runDevTeam({ interaction, query, relevantFileNames, repoName, branchName, thread }) {
  const queryToDisplay = `**user query**: ${query}. 
                          ${relevantFileNames ? '\n**relevant file names**: ' + relevantFileNames : ''} 
                          ${repoName ? '\n**repo name**: ' + repoName : ''}
                          ${branchName ? '\n**branch name**: ' + branchName : ''}
                          \nLooking through the code to investigate your query... give me a minute or so`;

  if (!thread) {
    await interaction.followUp({ content: queryToDisplay });
  } else {
    await thread.send(queryToDisplay);
  }

  try {
    let gptrResponse = await sendWebhookMessage({ query, relevantFileNames, repoName, branchName });

    if (gptrResponse && gptrResponse.rubber_ducker_thoughts) {
      let rubberDuckerChunks = '';
      let theGuidance = gptrResponse.rubber_ducker_thoughts;

      try {
        console.log('Original rubber_ducker_thoughts:', theGuidance);

        const repairedJson = jsonrepair(theGuidance);
        rubberDuckerChunks = splitMessage(JSON.parse(repairedJson).thoughts);
      } catch (error) {
        console.error('Error splitting messages:', error);
        rubberDuckerChunks = splitMessage(typeof theGuidance === 'object' ? JSON.stringify(theGuidance) : theGuidance);
      }

      for (const chunk of rubberDuckerChunks) {
        if (!thread) {
          await interaction.followUp({ content: chunk });
        } else {
          await thread.send(chunk);
        }
      }

      return true;
    } else {
      if (!thread) {
        return await interaction.followUp({ content: 'Invalid response received from GPTR.' });
      } else {
        return await thread.send('Invalid response received from GPTR.');
      }
    }
  } catch (error) {
    console.error({ content: 'Error handling message:', error });
    if (!thread) {
      return await interaction.followUp({ content: 'There was an error processing your request.' });
    } else {
      return await thread.send('There was an error processing your request.');
    }
  }
}

keepAlive();
client.login(process.env.DISCORD_BOT_TOKEN);