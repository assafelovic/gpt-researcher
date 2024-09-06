require('dotenv').config();
const Discord = require("discord.js");
const keepAlive = require("./server");
const { sendWebhookMessage } = require('./gptr-webhook');

const client = new Discord.Client();

function formatResponse(data) {
  // Extract the thoughts from the rubber ducker and tech lead review sections
  const rubberDuckerThoughts = JSON.parse(data.rubber_ducker_thoughts)
  const techLeadReview = JSON.parse(data.tech_lead_review)
  
  // Format the response string to include both thoughts
  const response = `
    **Rubber Ducker Thoughts:**
    ${rubberDuckerThoughts}

    **Tech Lead Review:**
    ${techLeadReview}
  `;
  
  return response;
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
      let formattedResponse = formatResponse(gptrResponse);
      return msg.channel.send(formattedResponse);
    } else {
      return msg.channel.send('Invalid response received from GPTR.');
    }
  } catch (error) {
    console.error('Error handling message:', error);
    return msg.channel.send('There was an error processing your request.');
  }
});

keepAlive();
client.login(process.env.DISCORD_BOT_TOKEN);
