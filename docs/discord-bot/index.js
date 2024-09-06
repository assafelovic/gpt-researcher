require('dotenv').config();
const Discord = require("discord.js")
const keepAlive = require("./server")
const { sendWebhookMessage } = require('./gptr-webhook');

const client = new Discord.Client()

client.on("ready", () => {
  console.log(`Logged in as ${client.user.tag}!`)
})

client.on("message", msg => {
  if (msg.author.bot) return

  // Send the message to GPTR via WebSocket
  sendWebhookMessage(msg.content);

  return msg.channel.send('sup')
  
//   db.get("responding").then(responding =>{
//     if (responding && sadWords.some(word => msg.content.includes(word))) {
//       db.get("encouragements").then(encouragements => {
//         const encouragement = encouragements[Math.floor(Math.random() * encouragements.length)]
//         msg.reply(encouragement)
//       })
//     }
//   })


//   if (msg.content.startsWith("$new")) {
//     encouragingMessage = msg.content.split("$new ")[1]
//     updateEncouragements(encouragingMessage)
//     msg.channel.send("New encouraging message added.")
//   }

//   if (msg.content.startsWith("$del")) {
//     index = parseInt(msg.content.split("$del ")[1])
//     deleteEncouragement(index)
//     msg.channel.send("Encouraging message deleted.")
//   }

//   if (msg.content.startsWith("$list")) {
//     db.get("encouragements").then(encouragements => {
//       msg.channel.send(encouragements)
//     })
//   }

//   if (msg.content.startsWith("$responding")) {
//     value = msg.content.split("$responding ")[1]

//     if (value.toLowerCase() == "true") {
//       db.set("responding", true)
//       msg.channel.send("Responding is on.")
//     } else {
//        db.set("responding", false)
//       msg.channel.send("Responding is off.")     
//     }
//   }

})

keepAlive()
client.login(process.env.DISCORD_BOT_TOKEN)