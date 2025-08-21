# webTODOtxt

webTODOtxt is a minimal, todo.txt-compatible task manager built with Flask. It supports multi-user setups, manages your tasks following the todo.txt format, and exposes a simple API for automation.

## 🧠 How It Works
Each user has a separate folder under `accounts/`, storing their todo.txt file and configuration.

The app follows the todo.txt format specification, supporting:
- Task priorities (A-Z)
- Creation dates
- Completion status
- Projects (+project)
- Contexts (@context)
You can automate task management by sending JSON requests with your user's API token.

```http
PUT /api/v1/<username>/todos
X-API-Key: your-api-key
Content-Type: application/json

{
  "task": "(A) 2025-08-21 Complete project documentation +work @computer"
}
```

## 🚀 Getting Started
1. Install Dependencies (inside root dir)

```bash
pip install -r .
```

2. Set Up Your App
Create a Python file `wsgi.py` with the following content (or modify according to your needs):
```bash
from webtodotxt import create_app
app = create_app("webtodotxt.config.ProductionHTTPSConfig")
```
Use Waitress and nginx for real production environment.

3. Set Environment Variables
Before running the app, set the required variables:
```bash
export SECRET_KEY="your-very-secret-key"
```
You can generate secret key with:
```bash
python -c 'import secrets; print(secrets.token_hex())'
```
__Changing the secret key invalidates all user API tokens.__

4. Run directly (local-only)
```bash
flask run
```

## 📁 Create the Accounts Directory
webTODOtxt stores user configurations and tasks inside a folder (default: `accounts/`). Create it manually or point to a custom path using `ACCOUNTS_DB_DIRECTORY_PATH` environment variable.

```bash
mkdir accounts
```

## 👤 Creating Users with the CLI
webTODOtxt comes with a built-in CLI to manage users.

```bash
python -m webtodotxt.cli init-user accounts
```

You will be prompted to enter:

- Username
- Full name
- Password (with confirmation)

Example output:

```bash
✅ User 'alice' initialized at accounts/alice/config.toml
🔑 API token: dGhpcy1pcy1hLXRva2Vu
```

Reset a User's Password:
```bash
python -m webtodotxt.cli reset-password accounts alice
```

## ✅ API (Optional Use)
You can automate task management by sending JSON requests with your user's API token.

The API supports the following endpoints:

```http
PUT /api/v1/<username>/todos
X-API-Key: your-api-key
Content-Type: application/json

{
  "task": "(A) 2025-08-21 Complete project documentation +work @computer",
  "raw": true
}
```