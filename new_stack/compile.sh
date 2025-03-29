#!/bin/sh
# Simple script to compile TypeScript to JavaScript
# This works on any platform with tsc installed

# Ensure the output directory exists
mkdir -p static/js

# Compile TypeScript to JavaScript
tsc -p tsconfig.json 