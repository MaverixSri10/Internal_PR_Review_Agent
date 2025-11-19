# AI-Powered Pull Request Review Agent

This project automates GitHub pull request reviews using **FastAPI**, **GitHub Webhooks**, and **AI (Copilot / OpenAI)**.  
It runs **static analysis (Semgrep, pip-audit)**, generates review insights, and posts **AI-generated comments** back to the PR.

---

## Workflow Overview

PR Opened  ➡️  Webhook Trigger (PR Opened → GitHub triggers webhook with FastAPI)
      ⬇️
Fetch PR Data from GitHub API (GitHub Service → Fetches PR diff & metadata)
      ⬇️
Run Static Analysis (Analysis Service → Runs Semgrep → pip-audit → nmp-audit)
      ⬇️
Combine Results → Create Review Prompt (Prompt Service → Merges results into AI prompt)
      ⬇️
Send Prompt to Copilot Agent (LLM) (LLM Service → Sends prompt to OpenAI)
      ⬇️
Post AI Review Comments on PR (GitHub Service → Posts comments to PR)

### Setup Instructions
1️. Clone the Repository
Pull request test
Hello Jay...
Added imported OS
API Key
code changed for open router
Added print statement
Changed LLM
Code changed
Added new review prompt 
Test case 1
Test Case 2 (Dummy Test)






 

