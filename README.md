# STEAM AI Assistant

A Python-based AI assistant that combines local knowledge base querying with LLM-powered responses via Ollama. The application runs in a Docker container with integrated Ollama support.

## Overview

STEAM AI provides two modes of interaction:

1. **Knowledge Base Mode** (default)
   - Query against a local STEAM knowledge base (Science, Technology, Engineering, Arts, Mathematics)
   - Context-aware search that matches queries to relevant knowledge files
   - Fast, deterministic responses based on stored content

2. **Study Mode**
   - Type `study` to activate STEAM_Study_Buddy
   - Connect to the Ollama API running in the container
   - Get AI-generated responses with a visual loading spinner
   - Useful for follow-up questions and conversational learning

## Features

- **Knowledge Base Storage**: Organized STEAM topics in the `/knowledge` folder
- **Context-Aware Search**: Automatically categorizes queries and matches them to relevant knowledge files
- **AI Integration**: Built-in support for the `llama3` model via Ollama
- **Docker Support**: Complete containerization with Ollama pre-configured
- **Ollama Readiness**: Automatic waiting and health checks before sending requests
- **Visual Feedback**: Animated spinner while waiting for Ollama responses
- **Color-coded Output**: Helpful terminal colors for different message types

## Prerequisites

- Docker and Docker CLI
- (Optional) Local Python 3.12+ with virtual environment for local development

## Quick Start

### Build the Docker Image

```bash
docker build --no-cache --pull -t steam_ai .
```

### Run the Container

**Interactive mode** (for testing):
```bash
docker run --rm -it -p 11434:11434 steam_ai
```

**Detached mode** (background):
```bash
docker run -d --name steam_ai -p 11434:11434 steam_ai
```

### Using the Application

Once running, you'll see the prompt `STEAM_AI>`.

#### Available Commands

- `help` - Display available commands
- `list` - List all knowledge files
- `read <filename>` - Display contents of a specific knowledge file
- `reload` - Reload knowledge files from disk
- `study` - Switch to STEAM_Study_Buddy mode
- `exit` - Exit the application

#### Example Usage

```
STEAM_AI> What is photosynthesis?
--- science.txt ---
Photosynthesis is the process by which plants convert light energy into chemical energy...

STEAM_AI> study
Study mode enabled. All following queries will be sent to Ollama.
STEAM_Study_Buddy> Explain photosynthesis in a way a 5-year-old would understand.
⠙ Waiting for response from Ollama...
[Ollama response appears after processing]
```

## Knowledge Base Structure

The application loads STEAM topics from the `/knowledge` folder:

- `science.txt` - Scientific concepts and principles
- `technology.txt` - Technology, computing, and digital topics
- `engineering.txt` - Engineering principles and design
- `arts.txt` - Arts, music, and creative topics
- `mathematics.txt` - Mathematical concepts and equations
- `greeting.txt` - Greeting responses

Edit or add files to customize the knowledge base.

## Docker Configuration

### Environment Variables

- `OLLAMA_HOST=0.0.0.0:11434` - Configure Ollama to listen on all interfaces
- `PATH` - Virtual environment is added to PATH for Python execution

### Exposed Ports

- `11434` - Ollama API port (required for Study Mode)

### What Happens on Container Start

1. Ollama server starts in the background
2. The container waits for Ollama to be ready
3. If `llama3` model is not present, it is pulled
4. The Python application starts and displays the prompt

## Local Development

### Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Locally

```bash
python main.py
```

**Note**: Study Mode requires Ollama running locally on `http://localhost:11434`.

## Dependencies

- `colorama` - Terminal color output
- `requests` - HTTP requests to Ollama API

See `requirements.txt` for full details.

## Troubleshooting

### "Error: unknown flag: --host"
The Ollama CLI uses environment variables, not command-line flags. The Dockerfile correctly sets `OLLAMA_HOST=0.0.0.0:11434`.

### "Could not connect to Ollama API"
This typically means Ollama is still starting. The readiness check will wait up to 60 seconds. If the error persists, check that port 11434 is available and not in use.

### "EOF when reading a line"
Make sure the container was started with the `-it` flags for interactive mode:
```bash
docker run --rm -it -p 11434:11434 steam_ai
```

### Model Takes Too Long to Load
The `llama3` model is large (~4.7 GB). Initial pulls may take several minutes depending on your internet connection.

## Project Structure

```
STEAM_AI/
├── main.py                 # Main application
├── Dockerfile              # Docker configuration
├── requirements.txt        # Python dependencies
├── knowledge/              # Knowledge base files
│   ├── science.txt
│   ├── technology.txt
│   ├── engineering.txt
│   ├── arts.txt
│   ├── mathematics.txt
│   └── greeting.txt
└── README.md               # This file
```

## Notes

- Study Mode queries are sent directly to Ollama; responses vary based on the model's generation parameters
- Knowledge Base Mode provides fast, deterministic answers
- The application is designed for educational STEAM topics but can be adapted for any knowledge domain
- Each Docker container run is isolated; the `llama3` model will be re-loaded unless using a persistent volume (see Docker docs)

## License

This project is provided as-is for educational purposes.
