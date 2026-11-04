# 🌐 Customer Quote-to-Provision Assistant

This repository contains the hackathon prototype for the **Customer Quote-to-Provision Assistant**. It is an AI-driven orchestrator designed to ingest natural language customer requirements and automatically translate them into a technical design, a Bill of Materials (BOM), a formal quote, and zero-touch provisioning API payloads for Lumen's Network-as-a-Service (NaaS) platform.

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Interactive Chat UI)
- **Backend:** Python
- **AI Orchestration:** Large Language Models (OpenAI / Gemini) for intent parsing

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your local machine:

- [Python 3.8 or higher](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- An API Key for your chosen LLM provider (e.g., OpenAI or Gemini API Key)

---

## 🚀 Local Setup Instructions

### 1. Clone the Repository

Open your terminal and clone the project to your local machine:

```bash
git clone https://github.com/s-vivek-55/q2p.git
cd q2p
```

### 2. Create and Activate a Virtual Environment

It is best practice to run this project in an isolated virtual environment.

**Windows (Git Bash / PowerShell):**

```bash
python -m venv venv
source venv/Scripts/activate
```

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

With your virtual environment activated, install the required Python packages:

```bash
pip install streamlit pydantic openai
```

### 4. Configure Environment Variables

Set your API key as an environment variable in your terminal before running the app.

**Windows / macOS / Linux (Git Bash):**

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 5. Run the Application

Start the Streamlit development server:

```bash
streamlit run app.py
```

This will automatically open a new tab in your default web browser pointing to http://localhost:8501.

---

## 💡 Usage Guide

- **Intake:** Type a natural language request in the chatbox (e.g., "I need a 10G connection to Azure with basic DDoS protection").
- **Review:** The AI parses your requirements and generates a Lumen-specific Bill of Materials and estimated MRC (Monthly Recurring Cost).
- **Provision:** Click "Approve & Provision Network" to simulate translating the BOM into Lumen NaaS orchestration API payloads.
