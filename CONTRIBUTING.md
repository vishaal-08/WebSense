# Contributing to WebSense

Thank you for your interest in contributing to WebSense! This project was built for Hackverse '26.

## Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/vishaal-08/WebSense.git
   cd WebSense
   ```

2. Set up the Python virtual environment for the backend:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

   pip install -r backend/requirements.txt
   ```

3. Load the Chrome extension:
   - Navigate to `chrome://extensions` in Google Chrome.
   - Enable **Developer mode** (top-right).
   - Click **Load unpacked** and select the `extension/` folder.

## Branch Workflow

- Create feature branches off `main`:
  ```bash
  git checkout -b feature/your-feature-name
  ```
- Keep changes focused and avoid modifying existing UI or working core logic unless fixing an issue.

## Testing Before PR

Always verify that the automated test suite passes before submitting a Pull Request:
```bash
# On Windows PowerShell:
$env:PYTHONPATH="backend"; python -m pytest backend/tests -v

# On macOS/Linux:
PYTHONPATH=backend python -m pytest backend/tests -v
```

Ensure all tests pass with zero failures.

## Commit & Pull Request Guidelines

- Use clear, descriptive commit messages (e.g. `fix: handle edge case in clause extractor`).
- Ensure no API keys, credentials, or sensitive files are committed.
- Keep PRs concise and link any relevant issue or description.
