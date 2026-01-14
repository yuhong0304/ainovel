from flask import Blueprint

def register_blueprints(app):
    from .settings import settings_bp
    from .project import project_bp
    from .world import world_bp
    from .generation import gen_bp
    from .export import export_bp
    from .learning import learning_bp

    app.register_blueprint(settings_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(world_bp)
    app.register_blueprint(gen_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(learning_bp)
