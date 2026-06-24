from flask import jsonify

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found", "status": 404}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error", "status": 500}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        print(f"[UNHANDLED ERROR] {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Unexpected error occurred", "status": 500}), 500
