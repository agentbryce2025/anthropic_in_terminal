# Example Claude Terminal Session

This document shows an example session using the terminal interface.

## Starting the Container

First, start the Docker container with the Anthropic Computer Use demo:

```bash
docker run -e ANTHROPIC_API_KEY=your_api_key_here \
  -v $HOME/.anthropic:/home/computeruse/.anthropic \
  -p 5900:5900 -p 8501:8501 -p 6080:6080 -p 8080:8080 \
  -it ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest
```

## Starting the Terminal Interface

Once inside the container, navigate to the directory containing the terminal_interface.py script:

```bash
cd /path/to/anthropic_in_terminal
./start_claude_terminal.sh YOUR_API_KEY
```

## Example Commands

Here are some sample commands to try:

1. **Basic question**:
   ```
   What is the current date?
   ```

2. **Take a screenshot**:
   ```
   Take a screenshot of the desktop
   ```

3. **Open Firefox and search for something**:
   ```
   Open Firefox and search for "Anthropic Claude API documentation"
   ```

4. **File operations**:
   ```
   Create a Python script that prints "Hello, World!"
   ```

5. **Save and load conversations**:
   ```
   /save my_conversation.json
   /load my_conversation.json
   ```

6. **Clear context**:
   ```
   /clear
   ```

7. **Exit the interface**:
   ```
   /exit
   ```

## Troubleshooting

If you encounter any issues:

1. Make sure you're running the script inside the container
2. Verify your API key is correct
3. Check that the path to the anthropic-quickstarts repo is correct
4. Try the `/clear` command to reset the context