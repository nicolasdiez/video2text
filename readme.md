# 🚀 PostPilotApp (formerly video2text)

An AI-driven content repurposing engine designed to automatically transform YouTube videos into highly engaging, scheduled Twitter/X threads and posts. 

Beyond standard generation, PostPilotApp implements a **Performance-Weighted RAG (Retrieval-Augmented Generation) feedback loop**, allowing the system to autonomously learn from past successful content to continuously improve its output quality. It is built with enterprise-grade software patterns, specifically **Domain-Driven Design (DDD)** and **Hexagonal Architecture (Ports & Adapters)**.

---

## 🎯 Functional Overview

The application operates through **4 fully automated, interconnected pipelines**. 
The core generation flow is completely decoupled from the continuous learning mechanism:

### 1. ✍️ Generation Pipeline (The Active Creator)
This is the entry point for new content creation, handling everything from raw video ingestion to final text generation.
* **Extraction & Transcription:** Connects directly to YouTube to retrieve video data, extracts the audio, and processes it using Whisper ASR (or Captions API) to generate a highly accurate text transcript of the new video.
* **Smart Context Retrieval (Performance-RAG):** Using the newly generated transcript, the system queries the vector database for past transcripts that share the highest semantic similarity.
* **Performance Filtering:** It retrieves the historical tweets associated with those similar past transcripts and filters them based on their real-world performance (Growth Score), provided by the Stats Pipeline.
* **LLM Synthesis:** The LLM (OpenAI/Gemini) is prompted with the *new transcript* (as the base) AND the *high-performing historical tweets* (as context/few-shot examples). This ensures the AI mimics the exact style of content that is mathematically proven to work.
* **Quality Assurance:** Passes the generated content through an Output Guardrail Service to ensure it meets strict platform constraints (character limits, formatting).

### 2. 🧠 Embeddings Pipeline (The Semantic Memory)
This pipeline operates as an asynchronous background knowledge engine, maintaining the vector database that powers the Generation Pipeline's RAG capabilities.
* **Dual-Vectorization:** It continuously generates and stores mathematical vector embeddings for **both** the saved video transcripts and the **historically published tweets**. 
* **Feedback Loop Enablement:** By vectorizing successful content and tying it to its source transcript, this pipeline builds the semantic index that allows the system to autonomously learn from its own past successes.

### 3. 🚀 Publishing Pipeline (The Distributor)
Handles the complex logistics of social media distribution.
* **OAuth Management:** Securely manages Twitter/X OAuth 1.0a and OAuth 2.0 user tokens.
* **Automated Scheduling:** Reads the user's scheduler runtime status and automatically publishes the approved content directly to the creator's timeline without manual intervention.

### 4. 📊 Stats Pipeline (The Evaluator)
The analytics engine that closes the learning loop.
* **Performance Tracking:** Scrapes and tracks the engagement metrics (likes, retweets, replies, bookmarks) of the published content using Twitter APIs and Apify.
* **Growth Scoring:** Calculates a Growth Score for every published tweet. This score is attached to the tweet's embedding in the database, actively dictating which tweets the Generation Pipeline will select as winning examples in the future.

---

## 🛠️ Technical Architecture

PostPilotApp is built using **Domain-Driven Design (DDD)** and **Hexagonal Architecture (Ports and Adapters)**. 
This strict boundary management ensures that the core business logic remains completely decoupled from external frameworks, databases, or third-party APIs.

### 🏗️ Core Layers

* **Domain Layer:** Contains the pure business rules and logic. Includes Entities (`User`, `Tweet`, `Video`, `MasterPrompt`), Value Objects (`EmbeddingVector`), and Domain Services (`PromptComposerService`, `GrowthScoreCalculatorService`).
* **Application Layer:** Orchestrates the use cases. This is where the 4 main Pipeline Services (`embeddings`, `generation`, `publishing`, `stats`) live, interacting solely with domain objects and interface ports.
* **Adapters (Inbound / Primary):** Driving the application.
  * **HTTP API:** RESTful endpoints built with **FastAPI** to interface with frontends, schedulers, or webhooks.
* **Adapters (Outbound / Secondary):** Driven by the application.
  * **Databases:** **MongoDB** repositories implementing data persistence and Vector Search.
  * **LLM Clients:** Implementations for **OpenAI** and **Google Gemini** to handle AI generation.
  * **External APIs:** Twitter publication clients, YouTube video clients, and Whisper ASR transcription services.

### 💻 Tech Stack & Infrastructure

* **Backend:** Python 3, FastAPI, Pydantic (Data Validation).
* **Database:** MongoDB (NoSQL) & Vector Storage.
* **AI & Machine Learning:** OpenAI API, Google Gemini API, Whisper ASR, RAG.
* **Security:** JWT (JSON Web Tokens) for authentication, Password Hashing, AES Encryption for API keys.
* **DevOps & Deployment:** * Containerized with **Docker**.
  * Orchestrated via **Kubernetes** (`deployment`, `service`, `ingress`, `configmap`).
  * CI/CD pipelines managed via **GitHub Actions** (`build-and-deploy.yaml`).

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Docker & Docker Compose
* MongoDB instance (with Vector Search capabilities)
* API Keys (OpenAI/Gemini, Twitter/X Developer, YouTube Data API)

### Local Development
1. Clone the repository: 
   git clone [https://github.com/nicolasdiez/post-pilot-app.git](https://github.com/yourusername/post-pilot-app.git)

2. Create your virtual environment and install dependencies:
    python -m venv post-pilot-app-venv
    #### On Windows:
    post-pilot-app-venv\Scripts\activate
    #### On macOS/Linux:
    source post-pilot-app-venv/bin/activate

    pip install -r requirements.txt

3.  Copy the environment template and fill in your credentials:
cp .env.example .env

4. Run the API:
uvicorn src.main:app --reload

--- 

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/nicolasdiez/post-pilot-app/issues).

---

## 📝 License

**© 2026 Nicolas Diez. All Rights Reserved.**

This repository and its contents are proprietary software. 

The source code is published here exclusively for portfolio, educational, and demonstration purposes. 

You are welcome to read and review the code for educational purposes. However, you are **NOT** permitted to use, copy, modify, merge, publish, distribute, sublicense, or sell copies of the software, or any part of it, for any commercial or non-commercial purposes without explicit written permission from the author.

---