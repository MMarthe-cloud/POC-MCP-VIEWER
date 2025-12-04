# Mobile Mapping Viewer - MCP

Talk to the map through an LLM. No clicks, just conversation.

## Setup

1. Create `.env` file in project root:
   ```
   GROQ_API_KEY=your_key_here
   ```

2. Install dependencies:
   ```bash
   # Backend (using uv)
   cd backend
   uv sync
   cd ..
   
   # Frontend
   cd frontend
   npm install
   cd ..
   ```

3. Run (2 terminals):
   ```bash
   # Terminal 1
   cd backend
   uv run uvicorn main:app --reload
   
   # Terminal 2
   cd frontend
   npm run dev
   ```

4. Open `http://localhost:5173`

## Test Questions

- "Show me all stop signs"
- "Which features are damaged?"
- "Show statistics by type"

