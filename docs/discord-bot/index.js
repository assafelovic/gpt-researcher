require('dotenv').config();
const { Client, GatewayIntentBits, ActionRowBuilder, Events, ModalBuilder, TextInputBuilder, TextInputStyle, ChannelType } = require('discord.js');
const keepAlive = require('./server');
const { sendWebhookMessage } = require('./gptr-webhook');
const { jsonrepair } = require('jsonrepair');
const { EmbedBuilder } = require('discord.js');

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

// Cooldown object to store the last message time for each channel
const cooldowns = {};

client.on('messageCreate', async message => {
  if (message.author.bot) return;
  // only share the /ask guide when a new message is posted in the help forum -  limit to every 30 minutes per post
  console.log(`Channel Data: ${message.channel.id}`);
  console.log(`Message Channel Data: ${console.log(JSON.stringify(message.channel, null, 2))}`);
  
  const channelId = message.channel.id;
  const channelParentId = message.channel.parentId;
  //return if its not posted in the help forum
  if(channelParentId != '1129339320562626580') return
  
  const now = Date.now();
  const cooldownAmount = 30 * 60 * 1000; // 30 minutes in milliseconds

  if (!cooldowns[channelId] || (now - cooldowns[channelId]) > cooldownAmount) {
    // await message.reply('please use the /ask command to launch a report by typing `/ask` into the chatbox & hitting ENTER.');

    const exampleEmbed = new EmbedBuilder()
      .setTitle('please use the /ask command to launch a report by typing `/ask` into the chatbox & hitting ENTER.')
      .setImage('https://media.discordapp.net/attachments/1127851779573420053/1285577932353568902/ask.webp?ex=66eb6fff&is=66ea1e7f&hm=32bc8335ed4c09c15a8541c058bbd513cf2ce757221a116d9c248c39a12d75df&=&format=webp&width=1740&height=704');
    
    message.channel.send({ embeds: [exampleEmbed] });
    cooldowns[channelId] = now;
  }
});


client.on(Events.InteractionCreate, async interaction => {
  if (interaction.isChatInputCommand()) {
    if (interaction.commandName === 'ask') {
      const modal = new ModalBuilder()
        .setCustomId('myModal')
        .setTitle('Ask the AI Researcher');

      const queryInput = new TextInputBuilder()
        .setCustomId('queryInput')
        .setLabel('Your question')
        .setStyle(TextInputStyle.Paragraph)
        .setPlaceholder('What are you exploring today / what tickles your mind?');

      const moreContextInput = new TextInputBuilder()
        .setCustomId('moreContextInput')
        .setLabel('Additional context (optional)')
        .setStyle(TextInputStyle.Paragraph)
        .setPlaceholder('Any additional context or details that would help us understand your question better?')
        .setRequired(false);

      const firstActionRow = new ActionRowBuilder().addComponents(queryInput);
      const secondActionRow = new ActionRowBuilder().addComponents(moreContextInput);

      modal.addComponents(firstActionRow, secondActionRow);

      await interaction.showModal(modal);
    }
  } else if (interaction.isModalSubmit()) {
    if (interaction.customId === 'myModal') {
      const query = interaction.fields.getTextInputValue('queryInput');
      const moreContext = interaction.fields.getTextInputValue('moreContextInput');

      let thread;
      if (interaction?.channel?.type === ChannelType.GuildText) {
        thread = await interaction.channel.threads.create({
          name: `Discussion: ${query.slice(0, 30)}...`,
          autoArchiveDuration: 60,
          reason: 'Discussion thread for the query',
        });
      }

      await interaction.deferUpdate();

      runDevTeam({ interaction, query, moreContext, thread })
        .catch(console.error);
    }
  }
});

async function runDevTeam({ interaction, query, moreContext, thread }) {
  const queryToDisplay = `**user query**: ${query}. 
                          ${moreContext ? '\n**more context**: ' + moreContext : ''} 
                          \nBrowsing the web to investigate your query... give me a minute or so`;

  if (!thread) {
    await interaction.followUp({ content: queryToDisplay });
  } else {
    await thread.send(queryToDisplay);
  }

  try {
    while (true) {
      const response = await sendWebhookMessage({ query, moreContext });
      
      if (response.type === 'progress') {
        // Handle progress updates
        const progressChunks = splitMessage(response.data);
        for (const chunk of progressChunks) {
          if (!thread) {
            await interaction.followUp({ content: chunk });
          } else {
            await thread.send(chunk);
          }
        }
      } else if (response.type === 'complete') {
        // Handle final result
        if (response.data && response.data.rubber_ducker_thoughts) {
          let rubberDuckerChunks = '';
          let theGuidance = response.data.rubber_ducker_thoughts;

          try {
            rubberDuckerChunks = splitMessage(theGuidance);
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
        }
        break; // Exit the loop when we get the final result
      }
    }

    return true;
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