require('dotenv').config();
const Discord = require("discord.js");
const keepAlive = require("./server");
const { sendWebhookMessage } = require('./gptr-webhook');

const client = new Discord.Client();

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

client.on("message", async msg => {
  if (msg.author.bot) return;

  msg.channel.send('Looking through the code to investigate your query... give me a minute or so');

  try {
    // Await the response from GPTR via WebSocket
    let gptrResponse = await sendWebhookMessage(msg.content);

    // Check if the response is valid
    if (gptrResponse && gptrResponse.rubber_ducker_thoughts && gptrResponse.tech_lead_review) {
      // Combine and split the messages into chunks
      const rubberDuckerChunks = splitMessage(gptrResponse.rubber_ducker_thoughts);
      const techLeadChunks = splitMessage(gptrResponse.tech_lead_review);

      // Send each chunk of Rubber Ducker Thoughts
      for (const chunk of rubberDuckerChunks) {
        await msg.channel.send(`**Rubber Duck Thoughts:**\n${chunk}`);
      }

      // Send each chunk of AI Tech Lead Thoughts
      for (const chunk of techLeadChunks) {
        await msg.channel.send(`**AI Tech Lead Thoughts:**\n${chunk}`);
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
