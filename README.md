# Generic Bot

A chatbot is a software or computer program that simulates human conversation or "chatter" through text or voice interactions.
Users in both business-to-consumer (B2C) and business-to-business (B2B) environments increasingly use chatbot virtual assistants to handle simple tasks. 
Generic Bot is software platform using which organization can create a Bot on their own without any need of technical team.

- - - -

## Requirements

Frameworks Used:

- Flask
- RASA

Database Used:

- MongoDB

Tools Used for  Deployment:

- Docker
- GIT Workflow

- - - -

### Smart Document Extractor Architecture: 

![smart_document_architechture](https://github.com/NikhilChandraDevarasetti/Hr_Bot/assets/78791882/323d8da3-df75-430b-84fd-cfdbd72c804d)


### Project Setup

To RUN this project install Docker on your system. Installation for docker can be found on this [link](https://docs.docker.com/engine/install/) .


- Build Docker container using following command

```
sudo docker build --no-cache 
```


- Use following command to Create Nginx Docker Container.

```
sudo docker build -t nginx:latest .
```


Above command will create 2 containers namely Hrbot & Mongo.
- Hrbot container will hold all the application related data & communication between the Flask app & RASA server.
- Mongo container will create Database named Hrbot with these three collection.These three collections hold login related , role related data & nlu data required for model training.


Mongo Collections  | 
------------- | 
admin_login   |
admin_role    |
nlu_data      |




- Run the created docker container using following command.

```
sudo docker run -it -d --publish 80:80 --publish 443:443  -v /neobot/nginx/neosoft.crt:/etc/ssl/certs/ssl-certificate.crt  -v /neobot/nginx/neosoft.key:/etc/ssl/private/ssl-key.key  -e SSL_CERTIFICATE=/etc/ssl/certs/ssl-certificate.crt  -e SSL_KEY=/etc/ssl/private/ssl-key.key  --net=host nginx:latest
```


- Once the container is built use below command to start the docker container. This will up your Flask App & Rasa Server.
```
sudo docker-compose up --detach
```


- We can make whole container down using below command.
```
sudo docker-compose down

```


#### Points to consider before building docker file for first time

1) Change permission of runner.sh file for first run.
2) If starting from scratch then first manually build docker otherwise it will fail in cicd pipeline since build time is more than 10 min.
3) bot/endpoints.yml is added in to .gitignore so we need to manually create this file on server

- - - -

### Project Components:

The whole project is divided based on 3 different types of Users where every user has different types of privileges.

Types of Users are:

<details>
<summary>Superadmin</summary>
<p>The main role of the Superadmin is to create different of users & assign roles with differnt priviledges to those users.</p>
<h6>Following list functionalities can be found under Superadmin Role:
    <ul>
      <li>Dashboard</li>
      <li>Create User</li>
      <li>User List</li>
      <li>Create Role</li>
      <li>Role List</li>
      <li>Staging Enviroment</li>
      <li>Production Enviroment</li>
    </ul>
</h6>
</details>

<details>
<summary>Author</summary>
<p>Author is responsible for overall developement of a chatbot. Author can trained a model using intent & response generation,create custom action to make api calls & story generation for dialogue management. </p>
<h6>Following list functionalities can be found under Superadmin Role:
    <ul>
      <li>Dashboard</li>
      <li>Create Intent</li>
      <li>Intent List</li>
      <li>Add Response</li>
      <li>Custom Action</li>
      <li>Story Listt</li>
      <li>Smart Document</li>
      <li>Trained Models</li>
      <li>Chat Audit</li>
    </ul>
</h6>
</details>


<details>
<summary>Tester</summary>
<p>Tester can test the working bots which are under production & staging.
</p>
</details>


 ---

### RASA Framework

```
Rasa is an open-source framework to build text and voice-based chatbots.
It's working at Level 3 of conversational AI, where the bot can understand 
the context.A level 3 conversational agent can handle things like the user 
changing their mind, handling context and even unexpected queries.
``````

### Chatbot Terminologies

Intent        | Response                   | Entities                                               | Stories                            | Custom Actions
------------- |----------------------------|--------------------------------------------------------|------------------------------------| -------------
What the user is implying  | Bot's response to the user | structured pieces of information inside a user message | Conversational Dialogue Management | Create API call



 ---
 
### Configurations:

Rasa Version      :         3.2.6


Minimum Compatible Version: 3.0.0


Rasa SDK Version  :         3.2.0


Python Version    :         3.9.13


Operating System  :         Linux-5.15.0-46-generic-x86_64-with-glibc2.31

---

# Hr_Bot
