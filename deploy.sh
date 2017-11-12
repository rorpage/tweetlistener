#!/bin/bash

docker service create --env-file env.list --network func_functions --name tweetlistener rorpage/tweetlistener:latest
