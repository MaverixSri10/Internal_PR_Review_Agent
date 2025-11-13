# 🤖 AI-Powered Pull Request Review Agent

This project automates GitHub pull request reviews using **FastAPI**, **GitHub Webhooks**, and **AI (Copilot / OpenAI)**.  
It runs **static analysis (Semgrep, pip-audit)**, generates review insights, and posts **AI-generated comments** back to the PR.

---

## 🚀 Workflow Overview

 PR Opened
     ⬇️
 Webhook Trigger
     ⬇️ 
 Fetch PR Data from GitHub API
     ⬇️ 
 Run Static Analysis (Semgrep, pip-audit, nmp-audit)
     ⬇️ 
 Combine Results → Create Review Prompt
     ⬇️ 
 Send Prompt to Copilot Agent (LLM)
     ⬇️ 
 Post AI Review Comments on PR

