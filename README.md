# Insurance Microservice

The purpose of this microservice is to listen for visit events from the core and generate insurance policies for clients automatically by using a selenium browser bot.

## Setup

After cloning from gitlab, first run the following command to build your docker environment

```
docker-compose build
```

This will start installing all locally needed python libaries as well as webdrivers for selenium.

After you have built your docker environment you will want to get a copy of the config.env file from another developer, this file is not included in the gitlab directory.

Once you have the config.env file you want to get your own core_api_key and place that inside the file. To get this key you want to use the program Postman found here https://www.postman.com/ once you have loaded up postman enter in the api url http://localhost:8000/api/clients/50/ and then enter your login information in the authroization tab, next hit send, if correct you will get a response back with all the json from the page. Once you have this go to headers tab and show auto-generated header and copy the value from the Authorziation key. Now paste that into your config.env file.

Dynamodb will be setup when you first run the docker container.

You may need to edit the docker-compose.yml file to change the networks variables or ports needed if another service is using that port.

## Development

First you must start the company core application first as this microservice depends on the network from the core appliation.

You can start the server by running:
```
docker-compose up -d
```

You should then be able to access the webserver at http://localhost:5000

You can access the dynamodb at localhost:8002

If you'd like a UI to help you understand dynamodb then why not try dynamodb-admin:
https://www.npmjs.com/package/dynamodb-admin

To run dynamodb-admin use the following command after running th:
```
DYNAMO_ENDPOINT=http://localhost:8002 dynamodb-admin
```

## KubeMQ

Kubernetes is our message queue system, whenever an event that needs any action is created on our service, our kubernetes system will handle the messaging between our services. Our core app is our publisher of events which will send events out to a designated channel

The core app currently sends events on the following channels.

- visit.accepted (Used whenever a visit is accepted by a client)
- visit.deleted (Used whenever a visit is cancelled by either a client or client)

Our microservice is set to subscribe to the channel `visit.*` this means that we will be listening to any event that is published on any channel that starts with `visit.`

# Crons

To run a cron you will need the following command
```
docker-compose run --rm web flask cron <cron name>
```

We currently have two crons, daily insurance and monthly insurance. They are runned by entering the above command and replacing `<cron name>` with daily or monthly respectfully.

# Endpoints

We have four endpoints setup on this microservice to be used by core to read data about a clients insurance status and their policies

- /clients (This displays all clients that are saved in our database)
- /clients/int:client_id (This will return data from the database about a specfic client) 
- /policies (This will return all polices)
- /policies/int:client_id/str:policy_start_date (This will return a specfic policy based on the start date and client id)

# Processes

![Screenshot_from_2021-07-19_18-57-12](/uploads/f42b3539c9dbce02e6da7fcfa7d961aa/Screenshot_from_2021-07-19_18-57-12.png)

Here shows the processes when we receive an event. If the event is a new accepted event we will then attempt to add in the visit into the database, if we are successful we will then try to add in a new client, if the client already exists we will then check if the start time of the visit is later than the client insured date if it is we will then get the end of the month for that visit and change the client insured end date to that.

If we receive a deleted visit event we will attempt to delete the visit from the database, we will first check if that visit is the last visit the client has chronologically, if it is we will then get the 2nd last visit they have and see if the start time is different from the client insured date, if it is we will then update it to the end of month for that visit, this is so we don't reinsure a client that has no upcoming visits.

![Insurance_Flow](/uploads/ff7546d71e8ed475ae24a2f4f2beace1/Insurance_Flow.png)

Here we have a diagram showing off the process of our crons on our system.

The daily insurance cron gets every uninsured client and checks to see if they have any accepted visits that happen tommorrow. If we do find any visits we will then run through the webdriver on the website surewise to create a policy for our client.

The monthly insurance gets all insured clients and checks to see if they have any upcomming visits in the next month. If they have upcoming visits we will then update their policy end date to be the last day of the next month. If they do not have any upcoming visits, we will then take find their latest policy to cancel it on the surewise website, once he have cancelled it we will then update the policy and clients insured status. Once we have done this for all insured clients we will then proceed to delete every past visit as we will no longer need the visit data.


