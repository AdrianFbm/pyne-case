"""Launch AIoli — the Jaffle Shop AI Assistant."""

import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app

app.run(debug=True, port=8050)
