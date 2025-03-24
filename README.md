# Anthropic Claude in Terminal

A terminal-based interface for interacting with Claude in the Anthropic Computer Use demo container.

## Overview

This project provides a command-line interface to interact with Claude's computer control capabilities without using the Streamlit web interface. It allows you to:

- Chat with Claude directly in your terminal
- See responses streaming in real-time
- Use all the same computer control tools (screenshot, mouse, keyboard, bash commands, etc.)
- Save and load conversations
- Clear context when needed

## Prerequisites

- The Anthropic computer-use-demo Docker container running
- Python 3.8+
- An Anthropic API key

## Usage

This script is designed to run inside the Anthropic computer-use-demo Docker container. First, start the container:

```bash
docker run -e ANTHROPIC_API_KEY=your_api_key_here \
  -v $HOME/.anthropic:/home/computeruse/.anthropic \
  -p 5900:5900 -p 8501:8501 -p 6080:6080 -p 8080:8080 \
  -it ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest
```

Then, inside the container, run the terminal interface:

```bash
python terminal_interface.py
```

You can also provide command-line arguments:

```bash
python terminal_interface.py --api-key your_api_key_here --model claude-3-7-sonnet-20250219
```

## Commands

While in the chat interface, you can use these special commands:

- `/clear` - Clear the chat history
- `/exit` - Exit the interface
- `/help` - Show help information
- `/save <filename>` - Save the current conversation to a file
- `/load <filename>` - Load a conversation from a file

## Features

- 🔄 Real-time streaming of Claude's responses
- 🛠️ Full access to all Claude computer control tools
- 💾 Conversation saving and loading
- 🧹 Context clearing
- 🎨 Colorized terminal output for better readability

## How It Works

This script interfaces directly with the Anthropic API using the same tools and components as the Streamlit interface in the original demo, but adapted for a terminal environment.

## License

This project is released under the MIT License - see the [LICENSE](LICENSE) file for details.