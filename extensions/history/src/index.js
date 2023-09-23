const express = require("express");
const mongoose = require('mongoose');
const amqp = require('amqplib');
const bodyParser = require("body-parser");
const {
    saveLog, saveReport
} = require('../controllers/content');

mongoose
    .connect(process.env.DATABASE_URL,  { useNewUrlParser: true, useCreateIndex: true, useFindAndModify: false })
    .then(() => console.log('DB connected'))
    .catch(err => {
        console.log(err);
    });

if (!process.env.RABBIT) {
    throw new Error("Please specify the name of the RabbitMQ host using environment variable RABBIT");
}

const RABBIT = process.env.RABBIT;

//
// Application entry point.
//
async function main() {

    const app = express();

    //
    // Enables JSON body parsing for HTTP requests.
    //
    app.use(bodyParser.json()); 
    
    //
    // Connects to the RabbitMQ server.
    //
    const messagingConnection = await amqp.connect(RABBIT); 

    //
    // Creates a RabbitMQ messaging channel.
    //
    const messageChannel = await messagingConnection.createChannel(); 

    //
    // Asserts that we have a "gpt-researcher" exchange.
    //
    await messageChannel.assertExchange("gpt-researcher", "fanout"); 

	//
	// Creates an anonyous queue.
	//
	const { queue } = await messageChannel.assertQueue("", { exclusive: false }); 

    console.log(`Created queue ${queue}, binding it to "gpt-researcher" exchange.`);
    
    //
    // Binds the queue to the exchange.
    //
    await messageChannel.bindQueue(queue, "gpt-researcher", "logs"); 

    //
    // Start receiving messages from the anonymous queue.
    //
    await messageChannel.consume(queue, async (msg) => {
        // console.log("Received a 'gpt-researcher' message:", msg);

        if(msg.content){
            const parsedMsg = JSON.parse(msg.content.toString()); // Parse the JSON message.
            // await historyCollection.insertOne({ videoId: parsedMsg.video.id }); // Record the "view" in the database.    
            console.log("Acknowledging message was handled: ",parsedMsg);
            if(parsedMsg.type=='finalReport'){
                saveReport({rabbitMessage: parsedMsg})
            } else {
                saveLog({rabbitMessage: parsedMsg})
            }
        }

        messageChannel.ack(msg); // If there is no error, acknowledge the message.
    });

    //
    // HTTP GET route to retrieve video viewing history.
    //
    app.get("/history", async (req, res) => {
        //
        // Retreives viewing history from database.
        // In a real application this should be paginated.
        //
        const history = await historyCollection.find().toArray(); 
        res.json({ history });
    });

    //
    // Starts the HTTP server.
    //
    app.listen(4000, () => {
        console.log("Microservice online.");
    });
}

main()
    .catch(err => {
        console.error("Microservice failed to start.");
        console.error(err && err.stack || err);
    });