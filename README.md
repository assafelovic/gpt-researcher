<a href="https://elest.io">
  <img src="https://elest.io/images/th3w1zard1.svg" alt="elest.io" width="150" height="75">
</a>

[![Discord](https://img.shields.io/static/v1.svg?logo=discord&color=f78A38&labelColor=083468&logoColor=ffffff&style=for-the-badge&label=Discord&message=community)](https://discord.gg/4T4JGaMYrD "Get instant assistance and engage in live discussions with both the community and team through our chat feature.")
[![th3w1zard1 examples](https://img.shields.io/static/v1.svg?logo=github&color=f78A38&labelColor=083468&logoColor=ffffff&style=for-the-badge&label=github&message=open%20source)](https://github.com/th3w1zard1-examples "Access the source code for all our repositories by viewing them.")
[![Blog](https://img.shields.io/static/v1.svg?color=f78A38&labelColor=083468&logoColor=ffffff&style=for-the-badge&label=elest.io&message=Blog)](https://blog.elest.io "Latest news about th3w1zard1, open source software, and DevOps techniques.")

# GPT researcher, verified and packaged by th3w1zard1

[GPT researcher](https://github.com/assafelovic/gpt-researcher), GPT based autonomous agent that does online comprehensive research on any given topic.

<img src="https://github.com/th3w1zard1-examples/gpt-researcher/raw/main/gpt-researcher.png" alt="gpt researcher" width="800">

Deploy a <a target="_blank" href="https://elest.io/open-source/gpt-researcher">fully managed neko</a> on <a target="_blank" href="https://elest.io/">elest.io</a> if you want automated backups, reverse proxy with SSL termination, firewall, automated OS & Software updates, and a team of Linux experts and open source enthusiasts to ensure your services are always safe, and functional.

[![deploy](https://github.com/th3w1zard1-examples/gpt-researcher/raw/main/deploy-on-th3w1zard1.png)](https://dash.elest.io/deploy?source=cicd&social=dockerCompose&url=https://github.com/th3w1zard1-examples/gpt-researcher)

# Why use th3w1zard1 images?

- th3w1zard1 stays in sync with updates from the original source and quickly releases new versions of this image through our automated processes.
- th3w1zard1 images provide timely access to the most recent bug fixes and features.
- Our team performs quality control checks to ensure the products we release meet our high standards.

# Usage

## Git clone

You can deploy it easily with the following command:

    git clone https://github.com/th3w1zard1-examples/gpt-researcher.git

Copy the .env file from tests folder to the project directory

    cp ./tests/.env ./.env

Edit the .env file with your own values.

Run the project with the following command

    docker-compose up -d

You can access the Web UI at: `http://your-domain:27938`

## Docker-compose

Here are some example snippets to help you get started creating a container.

    version: "3"
    services:
    gpt-researcher:
        image: th3w1zard1/gpt-researcher:${SOFTWARE_VERSION_TAG}
        environment:
            OPENAI_API_KEY: ${OPENAI_API_KEY}
            TAVILY_API_KEY: ${TAVILY_API_KEY}
        ports:
            - 172.17.0.1:27938:8000

### Environment variables

|       Variable       | Value (example) |
| :------------------: | :-------------: |
| SOFTWARE_VERSION_TAG |     latest      |
|    OPENAI_API_KEY    | YOUR_OPENAI_KEY |
|    TAVILY_API_KEY    | YOUR_TAVILY_KEY |

# Maintenance

## Logging

The th3w1zard1 GPT researcher Docker image sends the container logs to stdout. To view the logs, you can use the following command:

    docker-compose logs -f

To stop the stack you can use the following command:

    docker-compose down

## Backup and Restore with Docker Compose

To make backup and restore operations easier, we are using folder volume mounts. You can simply stop your stack with docker-compose down, then backup all the files and subfolders in the folder near the docker-compose.yml file.

Creating a ZIP Archive
For example, if you want to create a ZIP archive, navigate to the folder where you have your docker-compose.yml file and use this command:

    zip -r myarchive.zip .

Restoring from ZIP Archive
To restore from a ZIP archive, unzip the archive into the original folder using the following command:

    unzip myarchive.zip -d /path/to/original/folder

Starting Your Stack
Once your backup is complete, you can start your stack again with the following command:

    docker-compose up -d

That's it! With these simple steps, you can easily backup and restore your data volumes using Docker Compose.

# Links

- <a target="_blank" href="https://github.com/assafelovic/gpt-researcher">GPT researcher Github repository</a>

- <a target="_blank" href="https://github.com/th3w1zard1-examples/gpt-researcher">th3w1zard1/GPT researcher Github repository</a>
