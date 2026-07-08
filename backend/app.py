from flask import Flask, send_from_directory, Response, jsonify
from flask_cors import CORS
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routes.config_routes import config_bp
from routes.reservation_routes import reservation_bp
from routes.signin_routes import signin_bp
from routes.scheduler_routes import scheduler_bp
from routes.log_routes import log_bp


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    app.register_blueprint(config_bp)
    app.register_blueprint(reservation_bp)
    app.register_blueprint(signin_bp)
    app.register_blueprint(scheduler_bp)
    app.register_blueprint(log_bp)

    # 健康检查端点
    @app.route('/api/health')
    def health_check():
        return jsonify({
            "status": "ok",
            "service": "超星学习通座位预约管理系统",
            "version": "1.0.0",
            "timestamp": datetime.datetime.now(
                datetime.timezone(datetime.timedelta(hours=8))
            ).strftime("%Y-%m-%d %H:%M:%S")
        })

    @app.route('/')
    def index():
        static_folder = app.config.get('STATIC_FOLDER', '../frontend/dist')
        return send_from_directory(static_folder, 'index.html')

    @app.route('/<path:path>')
    def static_files(path):
        static_folder = app.config.get('STATIC_FOLDER', '../frontend/dist')
        return send_from_directory(static_folder, path)

    @app.errorhandler(404)
    def not_found(e):
        static_folder = app.config.get('STATIC_FOLDER', '../frontend/dist')
        return send_from_directory(static_folder, 'index.html')

    return app


app = create_app()

if __name__ == '__main__':
    print('🚀 超星学习通座位预约管理系统启动中...')
    print('📡 服务地址: http://localhost:5000')
    print('💚 健康检查: http://localhost:5000/api/health')
    print('🔧 按 Ctrl+C 停止服务')
    app.run(host='0.0.0.0', port=5000, debug=False)