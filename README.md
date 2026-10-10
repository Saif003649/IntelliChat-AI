# IntelliChat AI 🤖

A clean, modern, and lightweight AI chatbot built with **Streamlit**, **Google Gemini API**, and **SQLite**.

---

## 📁 Project Structure

This project follows a minimal, straightforward structure with only 4 essential files:

```text
chatbot-with-streamlit/
├── app.py              # Main application file (UI, Gemini API, SQLite chat history)
├── requirements.txt    # Python package dependencies
├── .env                # Local environment variables (Gemini API key)
├── .gitignore          # Git ignore rules for virtual environments, secrets & database
└── README.md           # Documentation and setup guide
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed on your system.

### 2. Install Dependencies
Open your terminal in the project directory and install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Configure Your Gemini API Key
You can configure your API key in either of two ways:

- **Option A (Recommended):** Add it directly to your `.env` file:
  ```env
  GEMINI_API_KEY=your_actual_api_key_here
  ```
- **Option B:** Launch the app and paste your API key inside the **API Key Settings** section in the sidebar.

> 💡 **Where to get a free key?**  
> Visit [Google AI Studio](https://aistudio.google.com/apikey) to generate a free Gemini API key.

### 4. Run the Application
Start the Streamlit development server:

```bash
streamlit run app.py
```

The application will launch automatically in your default browser at `http://localhost:8501`.

---

## ✨ Features

- **💬 Real-Time Streaming**: Live token-by-token response generation powered by Google's latest `gemini-3.8-flash` model.
- **💾 Automatic Chat History**: Persistent local storage using SQLite (`chat_history.db`). Chats are organized by topic.
- **⚡ Auto-Generated Titles**: Automatically generates smart, concise titles for your conversations.
- **🎛️ Model Controls**: Select between different Gemini models and adjust creativity via the temperature slider.
- **🎨 Sleek Dark UI**: Clean, responsive layout designed for ease of use without cluttered menus.
- **🗑️ Session Management**: Switch between past conversations, delete individual chats, or clear entire history in one click.

---

## 🛠️ Tech Stack

- **Frontend & App Framework**: [Streamlit](https://streamlit.io/)
- **AI Model**: [Google Generative AI](https://ai.google.dev/) (`gemini-3.8-flash`)
- **Database**: SQLite3 (built into Python)
- **Environment Management**: `python-dotenv`
