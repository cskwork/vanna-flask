# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vanna-Flask is a web server application that enables natural language chat with databases using AI. The system generates SQL queries from user questions, executes them, and provides visualizations. It's built with Flask as the web framework and integrates with multiple LLM providers (OpenAI, AWS Bedrock, Ollama, Google) and vector stores (ChromaDB) for AI-powered SQL generation.

## Core Architecture

- **Multi-LLM Support**: Configurable LLM backends through environment variables
- **Modular Configuration**: Dynamic class composition in `config.py` creates Vanna instances with different LLM and vector store combinations
- **Database Abstraction**: Supports SQLite, MySQL, and PostgreSQL through unified connection interface
- **Caching System**: In-memory caching for SQL queries, results, and visualizations
- **RESTful API**: Flask endpoints for SQL generation, execution, training, and visualization

### Key Components

1. **app.py**: Main Flask application with API endpoints
2. **config.py**: Configuration management and dynamic Vanna class creation
3. **cache.py**: Memory-based caching system with abstract interface
4. **train.py**: Database training script for DDL extraction and model training

## Development Commands

### Running the Application
```bash
# Local development
python app.py

# With Docker
docker build -t vanna-flask .
docker run -p 8080:8080 vanna-flask
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
```

### Training the Model
```bash
# Train on database schema
python train.py
```

## Configuration

The application uses environment variables for configuration. Key variables:

- **LLM**: `ollama` (default), `openai`, `bedrock`, `google`
- **VECTOR_STORE**: `chromadb` (default)
- **DATABASE**: `sqlite` (default), `mysql`, `postgresql`

See `.env.example` for complete configuration options.

## API Architecture

The Flask app provides a RESTful API with endpoints following the pattern `/api/v0/{action}`. Key endpoints:

- SQL generation from natural language questions
- SQL execution with result caching
- Plotly visualization generation
- Training data management
- CSV export functionality

The `@requires_cache` decorator ensures data consistency across related operations using unique request IDs.

## Database Integration

Connection parameters are determined by `get_db_connection_params()` which reads environment variables to configure database connections. The training script automatically extracts DDL for SQLite databases or requires manual DDL input for MySQL/PostgreSQL.

## Frontend

Static frontend files are served from the `/static` directory, providing a web interface for the chat functionality.