const express = require("express")

const server = express()

server.all("/", (req, res) => {
  res.send("Bot is running!")
})

function keepAlive() {
  server.listen(5000, () => {
    console.log("Server is ready.")
  })

  // Handle uncaught exceptions
  process.on("uncaughtException", (err) => {
    console.error("Uncaught Exception:", err);
    // Graceful shutdown logic
    // process.exit(1); // Exit process to trigger Docker's restart policy
  });

  // Handle unhandled promise rejections
  process.on("unhandledRejection", (reason, promise) => {
    console.error("Unhandled Rejection at:", promise, "reason:", reason);
    // Graceful shutdown logic
    // process.exit(1); // Exit process to trigger Docker's restart policy
  });
}

module.exports = keepAlive