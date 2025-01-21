## Discord Bot

Add a .env file in the root of the project and add the following:

```
DISCORD_BOT_TOKEN=
DISCORD_CLIENT_ID=
```

You can fetch the token from the Discord Developer Portal.

Go to: https://discord.com/developers/applications/

Click the "New Application" button and give your bot a name.

Within the Oath2 tab, you can generate a URL to invite your bot to your server.
First Select the "bot" scope.
<img src="./img/oath2-url-generator.png"></img>

Next, give your bot the proper permissions.

<img src="./img/bot-permissions.png"></img>

Finally you can invite your bot via the generated invite URL. In the case of the gptr-bot, here is the invite URL to open in your browser:

https://discord.com/oauth2/authorize?client_id=1281438963034361856&permissions=1689934339898432&integration_type=0&scope=bot

<br></br>
If you created your own custom bot, copy-paste the token into your .env file you created above.


## Deploying the bot commands

```bash
node deploy-commands.js
```

In our case, this will make the "ask" and "ping" commands available to users of the bot.


## Running the bot via Docker

```bash
docker compose --profile discord run --rm discord-bot
```

## Running the bot via CLI

```bash
# install dependencies
npm install

# run the bot
npm run dev
```

### Installing NodeJS and NPM on Ubuntu

```bash
#install nvm
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.4/install.sh | bash

export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm

# install nodejs
nvm install 18.17.0

# install npm
sudo apt-get install npm
```
