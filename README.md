# Vanna Flask

A web server for natural language database querying using AI. Chat with your database using plain English and get SQL queries, results, and visualizations automatically generated.

https://github.com/vanna-ai/vanna-flask/assets/7146154/5794c523-0c99-4a53-a558-509fa72885b9

## Features

- 🤖 **Multiple LLM Support**: OpenAI, AWS Bedrock, Ollama, Google AI
- 🗄️ **Multi-Database**: SQLite, MySQL, PostgreSQL
- 📊 **Auto Visualizations**: Generate Plotly charts from query results
- 🧠 **AI Training**: Train the model on your database schema
- 🚀 **Docker Ready**: Containerized deployment
- 💾 **Result Caching**: Efficient caching for repeated queries
- 🌐 **REST API**: Full API for integration

## Quick Start

### Option 1: Local Setup

1. **Clone and install dependencies**
```bash
git clone <repository-url>
cd vanna-flask
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

3. **Train the model (for SQLite)**
```bash
python train.py
```

4. **Run the server**
```bash
python app.py
```

### Option 2: Docker

```bash
docker build -t vanna-flask .
docker run -p 8080:8080 vanna-flask
```

The application will be available at `http://localhost:8080`

## Configuration

Configure via environment variables in `.env` file:

### LLM Provider
```bash
# Choose: ollama, openai, bedrock, google
LLM=ollama

# Ollama (default)
OLLAMA_MODEL=phi3

# OpenAI
# OPENAI_API_KEY=your_key
# OPENAI_MODEL=gpt-4

# AWS Bedrock
# BEDROCK_MODEL=anthropic.claude-v2

# Google AI
# GOOGLE_API_KEY=your_key
# GOOGLE_MODEL=gemini-pro
```

### Database
```bash
# Choose: sqlite, mysql, postgresql
DATABASE=sqlite

# SQLite (default)
SQLITE_PATH=my-database.sqlite

# MySQL
# MYSQL_HOST=localhost
# MYSQL_USER=user
# MYSQL_PASSWORD=password
# MYSQL_DATABASE=dbname

# PostgreSQL
# POSTGRES_HOST=localhost
# POSTGRES_USER=user
# POSTGRES_PASSWORD=password
# POSTGRES_DB=dbname
```

### Vector Store
```bash
VECTOR_STORE=chromadb
CHROMA_PATH=./chroma
```

## Training Your Model

Before using the application, train it on your database schema:

```bash
python train.py
```

- **SQLite**: Automatically extracts and trains on DDL
- **MySQL/PostgreSQL**: Manual DDL training required (see comments in train.py)

## API Endpoints

- `GET /api/v0/generate_questions` - Get sample questions
- `GET /api/v0/generate_sql?question=<query>` - Generate SQL from question
- `GET /api/v0/run_sql?id=<id>` - Execute generated SQL
- `GET /api/v0/generate_plotly_figure?id=<id>` - Create visualization
- `GET /api/v0/download_csv?id=<id>` - Download results as CSV
- `POST /api/v0/train` - Add training data
- `GET /api/v0/get_training_data` - View training data

## Usage Examples

1. **Ask a natural language question**: "Show me sales by month"
2. **Get generated SQL**: The AI converts your question to SQL
3. **View results**: Execute the query and see results in a table
4. **Get visualizations**: Automatically generate charts
5. **Download data**: Export results as CSV

## Architecture

- **Flask**: Web framework and API server
- **Vanna AI**: Core SQL generation engine
- **ChromaDB**: Vector storage for semantic search
- **Waitress**: Production WSGI server

## Troubleshooting

**Model not generating good SQL?**
- Run `python train.py` to train on your schema
- Add more training examples via the web interface

**Connection errors?**
- Check your database configuration in `.env`
- Ensure database is accessible and credentials are correct

**LLM errors?**
- Verify API keys are set correctly
- Check if the LLM service is available (especially for Ollama)