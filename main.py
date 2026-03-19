import os
import logging
from flask import Flask

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    from app.routes import webhook_bp, jobs_bp
    app.register_blueprint(webhook_bp)
    app.register_blueprint(jobs_bp)

    @app.route("/")
    def healthz():
        return "Bot is running.", 200

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
