#!/bin/bash

sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.9 python3.9-dev python3.9-venv -y
echo "alias python='/usr/bin/python3.9'" >> ~/.bashrc
