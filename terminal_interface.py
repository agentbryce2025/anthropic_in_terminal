#!/usr/bin/env python3
"""
Terminal interface for interacting with Claude in the computer-use-demo container.
This script provides a command-line interface to interact with Claude without using Streamlit.
"""

import argparse
import asyncio
import os
import json
import sys
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolUseBlockParam,
    BetaToolResultBlockParam,
)

# Import is handled dynamically to accommodate the container environment
# We need to add the anthropic-quickstarts path to the Python path
sys.path.append('/home/computeruse/anthropic-quickstarts')

# These imports will work inside the Docker container with the correct path setup
try:
    from computer_use_demo.tools import ToolResult, ToolVersion, TOOL_GROUPS_BY_VERSION
    from computer_use_demo.tools.collection import ToolCollection
    from computer_use_demo.loop import SYSTEM_PROMPT, APIProvider, _inject_prompt_caching, _response_to_params
except ImportError:
    print("Error: Could not import required modules from anthropic-quickstarts.")
    print("Make sure you're running this script inside the Docker container")
    print("or that the anthropic-quickstarts repository is in the correct location.")
    sys.exit(1)

# Constants
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
DEFAULT_MODEL = "claude-3-7-sonnet-20250219"
DEFAULT_TOOL_VERSION = "computer_use_20250124"
DEFAULT_MAX_TOKENS = 16384


class TerminalColors:
    """Terminal colors for better readability."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GRAY = '\033[90m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class TerminalInterface:
    """Terminal interface for interacting with Claude."""

    def __init__(self, api_key: str, model: str, tool_version: str):
        """Initialize the terminal interface."""
        self.api_key = api_key
        self.model = model
        self.tool_version = tool_version
        self.messages: List[BetaMessageParam] = []
        self.client = Anthropic(api_key=api_key, max_retries=4)
        self.tool_group = TOOL_GROUPS_BY_VERSION[self.tool_version]
        self.tool_collection = ToolCollection(*(ToolCls() for ToolCls in self.tool_group.tools))
        
        # Build the system prompt
        self.system = BetaTextBlockParam(
            type="text",
            text=SYSTEM_PROMPT,
        )

    def print_banner(self):
        """Print a banner with instructions."""
        print(f"\n{TerminalColors.BOLD}===== Claude Terminal Interface ====={TerminalColors.ENDC}")
        print(f"{TerminalColors.GRAY}Commands:{TerminalColors.ENDC}")
        print(f"  {TerminalColors.YELLOW}/clear{TerminalColors.ENDC} - Clear chat history")
        print(f"  {TerminalColors.YELLOW}/exit{TerminalColors.ENDC} - Exit the interface")
        print(f"  {TerminalColors.YELLOW}/help{TerminalColors.ENDC} - Show this help message")
        print(f"  {TerminalColors.YELLOW}/save <filename>{TerminalColors.ENDC} - Save conversation to file")
        print(f"  {TerminalColors.YELLOW}/load <filename>{TerminalColors.ENDC} - Load conversation from file")
        print(f"{TerminalColors.BOLD}================================={TerminalColors.ENDC}\n")

    def print_tool_result(self, result: ToolResult):
        """Print the result of a tool execution."""
        if result.error:
            print(f"{TerminalColors.RED}[Tool Error] {result.error}{TerminalColors.ENDC}")
            return
        
        if result.output:
            print(f"{TerminalColors.GRAY}[Tool Output]{TerminalColors.ENDC}")
            print(result.output)
        
        if result.base64_image:
            print(f"{TerminalColors.GRAY}[Tool Generated Image] (Base64 data not shown){TerminalColors.ENDC}")

    async def handle_command(self, command: str) -> bool:
        """Handle special commands that start with '/'."""
        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()
        
        if cmd == "/exit":
            print("Exiting...")
            return False
        elif cmd == "/clear":
            self.messages = []
            print("Chat history cleared.")
        elif cmd == "/help":
            self.print_banner()
        elif cmd == "/save":
            if len(cmd_parts) < 2:
                print(f"{TerminalColors.RED}Error: Please provide a filename to save to.{TerminalColors.ENDC}")
                return True
            
            filename = cmd_parts[1]
            try:
                with open(filename, 'w') as f:
                    # Convert messages to a serializable format
                    serializable_messages = []
                    for msg in self.messages:
                        serializable_msg = {
                            "role": msg["role"],
                            "content": msg["content"] if isinstance(msg["content"], str) else json.dumps(msg["content"])
                        }
                        serializable_messages.append(serializable_msg)
                    
                    json.dump(serializable_messages, f, indent=2)
                print(f"Conversation saved to {filename}")
            except Exception as e:
                print(f"{TerminalColors.RED}Error saving conversation: {str(e)}{TerminalColors.ENDC}")
        elif cmd == "/load":
            if len(cmd_parts) < 2:
                print(f"{TerminalColors.RED}Error: Please provide a filename to load from.{TerminalColors.ENDC}")
                return True
            
            filename = cmd_parts[1]
            try:
                with open(filename, 'r') as f:
                    loaded_messages = json.load(f)
                    # Convert the loaded messages back to the expected format
                    self.messages = []
                    for msg in loaded_messages:
                        if isinstance(msg["content"], str) and msg["content"].startswith("["):
                            try:
                                msg["content"] = json.loads(msg["content"])
                            except:
                                pass
                        self.messages.append(msg)
                print(f"Conversation loaded from {filename}")
            except Exception as e:
                print(f"{TerminalColors.RED}Error loading conversation: {str(e)}{TerminalColors.ENDC}")
        else:
            print(f"{TerminalColors.RED}Unknown command: {cmd}{TerminalColors.ENDC}")
        
        return True

    def output_callback(self, content_block: BetaContentBlockParam):
        """Handle and print Claude's response as it's streamed."""
        if content_block["type"] == "text":
            print(f"{TerminalColors.GREEN}{content_block['text']}{TerminalColors.ENDC}", end="", flush=True)
        elif content_block["type"] == "tool_use":
            print(f"\n{TerminalColors.BLUE}[Using Tool: {content_block['name']}]{TerminalColors.ENDC}")
            print(f"{TerminalColors.BLUE}Input: {json.dumps(content_block['input'], indent=2)}{TerminalColors.ENDC}")
        elif content_block["type"] == "thinking":
            print(f"\n{TerminalColors.GRAY}[Thinking...]{TerminalColors.ENDC}")
            print(f"{TerminalColors.GRAY}{content_block['thinking']}{TerminalColors.ENDC}")

    async def tool_output_callback(self, result: ToolResult, tool_id: str):
        """Handle the output of a tool execution."""
        self.print_tool_result(result)
        return None

    async def api_response_callback(self, request, response, error):
        """Handle API response or errors."""
        if error:
            print(f"{TerminalColors.RED}API Error: {str(error)}{TerminalColors.ENDC}")
        return None

    async def run(self):
        """Run the main interaction loop."""
        self.print_banner()
        
        try:
            while True:
                # Get user input
                print(f"{TerminalColors.BLUE}You:{TerminalColors.ENDC} ", end="", flush=True)
                user_input = input().strip()
                
                # Check for special commands
                if user_input.startswith("/"):
                    if not await self.handle_command(user_input):
                        break
                    continue
                
                # Add user message to conversation
                self.messages.append({
                    "role": "user",
                    "content": [{"type": "text", "text": user_input}],
                })
                
                print(f"\n{TerminalColors.GREEN}Claude:{TerminalColors.ENDC} ", end="", flush=True)
                
                # Run the sampling loop with the current messages
                await self.sampling_loop()
                
                print("\n")  # Add a newline for better readability
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            print(f"{TerminalColors.RED}Error: {str(e)}{TerminalColors.ENDC}")

    async def sampling_loop(self):
        """
        A simplified version of the sampling_loop function from the original code.
        """
        while True:
            betas = [self.tool_group.beta_flag] if self.tool_group.beta_flag else []
            betas.append(PROMPT_CACHING_BETA_FLAG)
            
            _inject_prompt_caching(self.messages)
            system_with_cache = self.system.copy()
            system_with_cache["cache_control"] = {"type": "ephemeral"}
            
            try:
                # Call the API
                raw_response = self.client.beta.messages.with_raw_response.create(
                    max_tokens=DEFAULT_MAX_TOKENS,
                    messages=self.messages,
                    model=self.model,
                    system=[system_with_cache],
                    tools=self.tool_collection.to_params(),
                    betas=betas,
                    stream=True,
                )
                
                with raw_response as stream:
                    response_content_blocks = []
                    
                    async for chunk in stream:
                        if hasattr(chunk, 'delta') and chunk.delta:
                            if hasattr(chunk.delta, 'content') and chunk.delta.content:
                                for block in chunk.delta.content:
                                    # Handle text blocks streaming
                                    if block.type == "text" and hasattr(block, "text"):
                                        print(block.text, end="", flush=True)
                                    # Store all response blocks for later processing
                                    response_content_blocks.append(block)
                    
                    # Process the complete response after streaming
                    response_params = []
                    for block in response_content_blocks:
                        if block.type == "text":
                            if hasattr(block, "text") and block.text:
                                response_params.append({"type": "text", "text": block.text})
                        elif block.type == "tool_use":
                            # Convert the block to a dict
                            tool_use_block = {
                                "type": "tool_use",
                                "id": block.id,
                                "name": block.name,
                                "input": block.input,
                            }
                            response_params.append(tool_use_block)
                            # Run the tool
                            result = await self.tool_collection.run(
                                name=block.name,
                                tool_input=block.input,
                            )
                            await self.tool_output_callback(result, block.id)
                            
                            # Add tool result to messages
                            tool_result_content = []
                            is_error = False
                            
                            if result.error:
                                is_error = True
                                tool_result_content = result.error
                            else:
                                if result.output:
                                    tool_result_content.append({
                                        "type": "text",
                                        "text": result.output
                                    })
                                if result.base64_image:
                                    tool_result_content.append({
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/png",
                                            "data": result.base64_image,
                                        },
                                    })
                            
                            # Add tool result to messages
                            self.messages.append({
                                "content": [{
                                    "type": "tool_result",
                                    "content": tool_result_content,
                                    "tool_use_id": block.id,
                                    "is_error": is_error,
                                }],
                                "role": "user"
                            })
                
                # Add assistant's message to the conversation
                self.messages.append({
                    "role": "assistant",
                    "content": response_params,
                })
                
                # If there were no tool uses, we're done with this turn
                if not any(block.get("type") == "tool_use" for block in response_params if isinstance(block, dict)):
                    return
                
            except Exception as e:
                print(f"\n{TerminalColors.RED}Error calling Claude API: {str(e)}{TerminalColors.ENDC}")
                return


async def main():
    """Parse arguments and start the terminal interface."""
    parser = argparse.ArgumentParser(description="Terminal interface for interacting with Claude")
    parser.add_argument("--api-key", default=os.environ.get("ANTHROPIC_API_KEY"), 
                        help="Anthropic API key (default: ANTHROPIC_API_KEY env var)")
    parser.add_argument("--model", default=DEFAULT_MODEL, 
                        help=f"Model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--tool-version", default=DEFAULT_TOOL_VERSION, 
                        help=f"Tool version to use (default: {DEFAULT_TOOL_VERSION})")
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("Error: No API key provided. Set ANTHROPIC_API_KEY environment variable or use --api-key.")
        sys.exit(1)
    
    interface = TerminalInterface(
        api_key=args.api_key,
        model=args.model,
        tool_version=args.tool_version,
    )
    
    await interface.run()


if __name__ == "__main__":
    asyncio.run(main())