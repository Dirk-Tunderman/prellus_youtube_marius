#!/bin/bash

FRONTEND_DIR=frontend
BACKEND_DIR=app
VENV_DIR=$BACKEND_DIR/.venv

echo "Starting frontend..."
cd $FRONTEND_DIR && npm run dev &

echo "Starting backend..."
cd $BACKEND_DIR && source $VENV_DIR/bin/activate && python main.py

echo "Application started"
