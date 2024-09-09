require('dotenv').config();
const { Client, GatewayIntentBits, ActionRowBuilder, Events, ModalBuilder, TextInputBuilder, TextInputStyle } = require('discord.js');
const keepAlive = require("./server");
const { sendWebhookMessage } = require('./gptr-webhook');

// Define the intents your bot needs
const client = new Client({
  intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.MessageContent
  ],
});

function splitMessage(message, chunkSize = 1500) {
  const chunks = [];
  for (let i = 0; i < message.length; i += chunkSize) {
    chunks.push(message.slice(i, i + chunkSize));
  }
  return chunks;
}

client.on("ready", () => {
  console.log(`Logged in as ${client.user.tag}!`);
});

client.on(Events.InteractionCreate, async interaction => {
	if (!interaction.isChatInputCommand()) return;

  if(interaction.commandName === 'ping') {
    await interaction.reply('Pong!');
  }

	if (interaction.commandName === 'ask') {
		// Create the modal
		const modal = new ModalBuilder()
			.setCustomId('myModal')
			.setTitle('My Modal');

		// Add components to modal

		// Create the text input components
		const favoriteColorInput = new TextInputBuilder()
			.setCustomId('favoriteColorInput')
		    // The label is the prompt the user sees for this input
			.setLabel("What's your favorite color?")
		    // Short means only a single line of text
			.setStyle(TextInputStyle.Short);

		const hobbiesInput = new TextInputBuilder()
			.setCustomId('hobbiesInput')
			.setLabel("What's some of your favorite hobbies?")
		    // Paragraph means multiple lines of text.
			.setStyle(TextInputStyle.Paragraph);

		// An action row only holds one text input,
		// so you need one action row per text input.
		const firstActionRow = new ActionRowBuilder().addComponents(favoriteColorInput);
		const secondActionRow = new ActionRowBuilder().addComponents(hobbiesInput);

		// Add inputs to the modal
		modal.addComponents(firstActionRow, secondActionRow);

		// Show the modal to the user
		await interaction.showModal(modal);
	}
});

client.on(Events.InteractionCreate, async interaction => {
	if (!interaction.isModalSubmit()) return;
	if (interaction.customId === 'myModal') {
    const favoriteColor = interaction.fields.getTextInputValue('favoriteColorInput');
	  const hobbies = interaction.fields.getTextInputValue('hobbiesInput');
		await interaction.reply({ content: `
      Your favorite color is: ${favoriteColor}
      Your hobbies are: ${hobbies}  
    ` });
	}
});

client.on("message", async msg => {
  if (msg.author.bot) return;

  msg.channel.send('Looking through the code to investigate your query... give me a minute or so');

  try {
    // Await the response from GPTR via WebSocket
    let gptrResponse = await sendWebhookMessage(msg.content);

    // Check if the response is valid
    if (gptrResponse && gptrResponse.rubber_ducker_thoughts) {
      // Combine and split the messages into chunks
      const rubberDuckerChunks = splitMessage(JSON.parse(gptrResponse.rubber_ducker_thoughts).thoughts);

      // Send each chunk of Rubber Ducker Thoughts
      for (const chunk of rubberDuckerChunks) {
        await msg.channel.send(chunk);
      }

      return true;
    } else {
      return msg.channel.send("Invalid response received from GPTR.");
    }
  } catch (error) {
    console.error("Error handling message:", error);
    return msg.channel.send("There was an error processing your request.");
  }
});

keepAlive();
client.login(process.env.DISCORD_BOT_TOKEN);
