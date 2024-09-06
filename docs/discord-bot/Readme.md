
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

Next, add a .env file in the root of the project and add the following:

```
DISCORD_BOT_TOKEN=
```

You can fetch the token from the Discord Developer Portal.
<br>
Go to: https://discord.com/developers/applications/
<br>
Click the "New Application" button and give your bot a name.
<br>
Give your bot the proper permissions.
<br>
<img src="./bot-permissions.png">
<br>
Finally you can invite your bot & copy-paste the token into your .env file you created above.