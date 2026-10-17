# RPG Battle Simulator

## Browser version

Install the requirements and start the local Flask server:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> in your browser. The web game stores progress in
each visitor's signed browser session cookie, so visitors do not overwrite one
another's game. Clearing browser data clears that browser's game; progress does
not sync between browsers or devices. Do not put passwords or other secrets in
the game state.

For a local development server, `app.py` enables Flask debug mode only when run
directly. Do not use that development server or debug mode for public hosting.

### Deploying to PythonAnywhere

1. Push `app.py`, `rpg_game.py`, `templates/`, `static/`, and
   `requirements.txt` to GitHub.
2. In PythonAnywhere, open a Bash console and clone your repository. For example:

   ```bash
   git clone https://github.com/Frogs-are-cool/RPG-battle-simulator-project.git
   cd RPG-battle-simulator-project
   mkvirtualenv --python=/usr/bin/python3.13 rpg-web
   pip install -r requirements.txt
   ```

   Choose a Python version available in your PythonAnywhere account; use that
   same version when creating the web app.
3. In the **Web** tab, add a **Manual Configuration** web app, select the same
   Python version, and set its virtualenv to `rpg-web`. Set the source/working
   directory to the cloned project directory.
4. Edit the WSGI configuration file linked from the Web tab. Replace its
   example application code with the following, substituting your PythonAnywhere
   username and project directory:

   ```python
   import os
   import sys

   project_home = "/home/YOURUSERNAME/RPG-battle-simulator-project"
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   os.environ["FLASK_SECRET_KEY"] = "PASTE_A_PRIVATE_RANDOM_SECRET_HERE"
   os.environ["FLASK_COOKIE_SECURE"] = "1"

   from app import app as application
   ```

   Generate the secret in a PythonAnywhere Bash console with
   `python -c "import secrets; print(secrets.token_hex(32))"`. Keep it private:
   don't add it to GitHub or share it. Use the WSGI file, not `app.run()`, to
   serve the deployed site.
5. Click **Reload** in the Web tab and open the web app's
   `YOURUSERNAME.pythonanywhere.com` address. Check the Web tab error log if
   the page doesn't load.

The free account's current web-app and outbound-network limits may change;
check PythonAnywhere's plan details before deployment.

## Desktop and console versions

The desktop UI uses Tkinter:

```bash
python3 rpg_ui.py
```

The original console game is also available:

```bash
python3 rpg_game.py
```

These local versions use `rpg_save/save.json` beside the script. The browser
version does not use that shared save file.
