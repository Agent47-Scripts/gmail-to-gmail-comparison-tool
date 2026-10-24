# Gmail to Gmail Comparison & Audit Tool

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-orange.svg?style=flat-square&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/agent47)

> **Purpose:** A lightweight, dependency-free Python utility designed to compare, audit, and verify email message counts and folder structures side-by-side between two Gmail or Google Workspace accounts (e.g., primary account vs. backup account, or post-migration audit).

## 🚀 Key Features

* **Cross-Platform Compatibility:** Runs natively on **Linux, macOS, and Windows (10/11)** using only standard Python 3 libraries (`imaplib`, `ssl`, `os`, `sys`).

* **Side-by-Side Comparison:** Scans both source and target Gmail accounts simultaneously and generates a clear ASCII report showing folder message counts and discrepancies.

* **Backup & Migration Audit:** Perfect for validating that a Gmail-to-Gmail backup or migration process was 100% complete with zero missing emails.

* **Security First:** Authenticates using environment variables and Google App Passwords without hardcoding sensitive details in scripts.

## 🔑 Authentication Setup (Google App Passwords)

To allow the script to securely query your Gmail accounts over IMAP, you must generate an **App Password** for both accounts:

1. Enable **2-Step Verification** in your [Google Account Security Settings](https://myaccount.google.com/security).

2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords).

3. Create a new app password (e.g., named "Gmail Comparison Tool").

4. Copy the **16-character code** (e.g., `abcd1234efgh5678`).

## ⚙️ Usage Instructions

Set the credentials for both Gmail accounts as environment variables and run `gmail-to-gmail-comparison-tool.py`:

### Option A: Linux / macOS (Terminal)

```bash
# Source Gmail Account
export SRC_HOST="imap.gmail.com"
export SRC_USER="source-account@gmail.com"
export SRC_PASS="abcd1234efgh5678"

# Target / Backup Gmail Account
export TGT_HOST="imap.gmail.com"
export TGT_USER="backup-account@gmail.com"
export TGT_PASS="ijkl5678mnop1234"

# Run Comparison
python3 gmail-to-gmail-comparison-tool.py
```

### Option B: Windows CMD (Command Prompt)

```cmd
:: Source Gmail Account
set SRC_HOST=imap.gmail.com
set SRC_USER=source-account@gmail.com
set SRC_PASS=abcd1234efgh5678

:: Target / Backup Gmail Account
set TGT_HOST=imap.gmail.com
set TGT_USER=backup-account@gmail.com
set TGT_PASS=ijkl5678mnop1234

:: Run Comparison
python gmail-to-gmail-comparison-tool.py
```

### Option C: Windows PowerShell

```powershell
# Source Gmail Account
$env:SRC_HOST="imap.gmail.com"
$env:SRC_USER="source-account@gmail.com"
$env:SRC_PASS="abcd1234efgh5678"

# Target / Backup Gmail Account
$env:TGT_HOST="imap.gmail.com"
$env:TGT_USER="backup-account@gmail.com"
$env:TGT_PASS="ijkl5678mnop1234"

# Run Comparison
python gmail-to-gmail-comparison-tool.py
```

## 📊 Sample Output

```text
============================================================
Folder Name                         | Source   | Target   | Status
============================================================
INBOX                               | 1250     | 1250     | MATCH OK
Sent Mail                           | 840      | 840      | MATCH OK
Archive                             | 3120     | 3120     | MATCH OK
Work/Projects                       | 150      | 150      | MATCH OK
============================================================
[+] Audit Success: All folder counts match perfectly!
```

## ☕ Support & Feedback

If this tool saved you time or helped verify your email backups, feel free to drop a star on GitHub or support the project:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-orange.svg?style=flat-square&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/agent47)

## 📜 License

Licensed under the [MIT License](LICENSE). Free to use, modify, and distribute.