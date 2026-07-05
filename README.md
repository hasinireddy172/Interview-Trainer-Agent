# AI Interview Trainer Agent
### Powered by IBM Granite on watsonx.ai

A production-ready, AI-powered Interview Trainer web application built with Python Flask and IBM watsonx.ai Granite models. Upload your resume, specify a target job role, and get hyper-personalised HR, Technical, and Behavioral interview questions complete with model answers and a preparation guide — all enhanced by Retrieval-Augmented Generation (RAG).

---

## Features

| Feature | Description |
|---|---|
| **Resume Parsing** | Upload a PDF resume; IBM Granite extracts name, skills, experience, education, projects, and certifications |
| **Job Role Targeting** | Enter any job role (Software Engineer, Data Scientist, Product Manager, etc.) |
| **HR Questions** | 5 personalised situational/HR questions with model answers |
| **Technical Questions** | 6 difficulty-tiered technical questions (Foundational → Advanced) |
| **Behavioral Questions** | 5 STAR-method behavioral questions tied to core competencies |
| **Preparation Tips** | Strengths analysis, gap identification, day-before/day-of tips, salary negotiation advice |
| **RAG Knowledge Base** | Upload PDF/TXT interview guides to enrich AI answers via ChromaDB vector search |
| **IBM Granite Model** | Uses `ibm/granite-3-3-8b-instruct` (configurable in `.env`) |
| **Loading Animations** | Animated three-ring spinner with progress bar during AI generation |
| **Mobile Responsive** | Bootstrap 5 + custom CSS, fully responsive on all screen sizes |
| **Customisable Agent** | Edit `agent_instructions.py` to change persona, prompts, and behaviour |

---

## Project Structure

```
interview-trainer/
├── app.py                   # Flask backend (all routes)
├── watsonx_client.py        # IBM watsonx.ai Granite wrapper
├── rag_utils.py             # RAG: ChromaDB ingestion & retrieval
├── agent_instructions.py    # ← Edit here to customise agent behaviour
├── requirements.txt
├── .env.example             # Copy to .env and fill credentials
├── .env                     # Your actual credentials (git-ignored)
├── README.md
│
├── templates/
│   ├── base.html            # Base template (navbar, footer)
│   └── index.html           # Main application page
│
├── static/
│   ├── css/style.css        # Custom styling
│   └── js/main.js           # Frontend logic
│
├── uploads/                 # Temporary upload directory (auto-created)
└── chroma_db/               # ChromaDB persistent vector store (auto-created)
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd interview-trainer
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure IBM watsonx.ai Credentials

```bash
cp .env.example .env
```

Edit `.env`:

```env
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

**Getting IBM watsonx.ai credentials:**
1. Log in to [IBM Cloud](https://cloud.ibm.com)
2. Create a **Watson Machine Learning** service instance
3. Go to [watsonx.ai](https://dataplatform.cloud.ibm.com/wx/home) → Projects → your project → Manage → General → Project ID
4. Create an IBM Cloud API key: My IBM → Profile → API keys → Create

### 3. Run the Application

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

### 4. Production Deployment

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## Configuration

All AI behaviour is controlled through `agent_instructions.py`. You can modify:

| Constant | Purpose |
|---|---|
| `AGENT_PERSONA` | The AI coach's personality and background |
| `RESUME_EXTRACTION_PROMPT` | How the resume is parsed |
| `HR_QUESTIONS_PROMPT` | HR question generation instructions |
| `TECHNICAL_QUESTIONS_PROMPT` | Technical question generation + difficulty |
| `BEHAVIORAL_QUESTIONS_PROMPT` | STAR-method behavioral questions |
| `PREPARATION_TIPS_PROMPT` | Prep guide generation |
| `QUESTION_CATEGORIES` | Registry of active question categories |
| `RAG_CHUNK_SIZE` | Document chunking size for RAG |
| `RAG_TOP_K` | Number of RAG chunks retrieved per query |

### Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `WATSONX_API_KEY` | — | IBM Cloud API key (required) |
| `WATSONX_PROJECT_ID` | — | watsonx.ai project ID (required) |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | watsonx.ai endpoint URL |
| `GRANITE_MODEL_ID` | `ibm/granite-3-3-8b-instruct` | IBM Granite model to use |
| `MAX_NEW_TOKENS` | `2048` | Maximum tokens per generation |
| `TEMPERATURE` | `0.7` | Generation creativity (0.0–1.0) |
| `MAX_UPLOAD_MB` | `16` | Maximum upload file size |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Home page |
| `POST` | `/upload_resume` | Upload and parse PDF resume |
| `POST` | `/generate_questions` | Generate interview questions |
| `POST` | `/generate_tips` | Generate preparation tips |
| `POST` | `/upload_kb` | Add document to knowledge base |
| `GET` | `/kb_status` | Knowledge base chunk count |
| `POST` | `/clear_kb` | Clear the knowledge base |
| `GET` | `/health` | Health check |

---

## Using the Knowledge Base (RAG)

1. Scroll to the **Knowledge Base** section
2. Upload PDF or TXT files (interview guides, company documents, study notes)
3. The system chunks and embeds them using `all-MiniLM-L6-v2` into ChromaDB
4. Relevant chunks are automatically retrieved and injected into prompts when generating questions

---

## Supported IBM Granite Models

| Model ID | Description |
|---|---|
| `ibm/granite-3-3-8b-instruct` | **Recommended** — Fast, high-quality |
| `ibm/granite-3-2-8b-instruct` | Granite 3.2 generation |
| `ibm/granite-13b-chat-v2` | 13B chat model |
| `ibm/granite-34b-code-instruct` | Code-focused, great for technical Qs |

Change the model by updating `GRANITE_MODEL_ID` in your `.env` file.

---

## Troubleshooting

**`EnvironmentError: WATSONX_API_KEY and WATSONX_PROJECT_ID must be set`**
→ Copy `.env.example` to `.env` and fill in your IBM credentials.

**`Could not extract text from the PDF`**
→ The PDF may be a scanned image. Use a text-based PDF or OCR it first.

**`Model generation failed`**
→ Check your API key, project ID, and that your watsonx.ai project has the Granite model enabled.

**ChromaDB errors on first run**
→ The `chroma_db/` directory is created automatically. Ensure write permissions.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with IBM Granite AI on watsonx.ai*
