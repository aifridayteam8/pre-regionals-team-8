from flask import Flask
from flask_cors import CORS

from api.routes import api


def create_app() -> Flask:
    app = Flask(__name__)
    # Frontend is a separate app on a different origin — allow cross-origin calls.
    CORS(app)
    app.register_blueprint(api, url_prefix="/api")
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
