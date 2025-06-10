#!/bin/bash

export PYTHONIOENCODING=UTF-8
export PYTHONPATH=$PYTHONPATH:plugins


exec ./bin/server_exec -worker default
