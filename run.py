#!/usr/bin/env python
"""
Run the Group Navigation app with WebSocket support
"""
from app import create_app

if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(app, host='127.0.0.1', port=5000, debug=False)
