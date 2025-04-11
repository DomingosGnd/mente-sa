from flask import Flask, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, Usuario, Profissional, Administrador, Meditacao
from routes import init_routes
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mentesadb.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    logger.debug(f"Tentando carregar usuário com ID: {user_id} da sessão: {session.get('_user_id')}")
    user_type = session.get('user_type')
    logger.debug(f"Tipo de usuário na sessão: {user_type}")
    if user_type == 'Usuario':
        user = Usuario.query.get(int(user_id))
    elif user_type == 'Profissional':
        user = Profissional.query.get(int(user_id))
    elif user_type == 'Administrador':
        user = Administrador.query.get(int(user_id))
    else:
        logger.debug("Tipo de usuário não encontrado na sessão, tentando todas as tabelas")
        for model in [Usuario, Profissional, Administrador]:
            user = model.query.get(int(user_id))
            if user:
                session['user_type'] = model.__name__
                logger.debug(f"Usuário encontrado: {user.email} ({model.__name__}, ID={user.id})")
                return user
        user = None
    if user:
        logger.debug(f"Usuário encontrado: {user.email} ({user_type}, ID={user.id})")
        return user
    logger.debug("Nenhum usuário encontrado")
    return None

with app.app_context():
    db.drop_all()
    db.create_all()
    # Adicionar meditações iniciais
    if not Meditacao.query.first():
        meditacoes = [
            Meditacao(titulo="Relaxamento Básico", descricao="Meditação de 10 minutos para iniciantes", url="https://example.com/relaxamento.mp3"),
            Meditacao(titulo="Foco e Concentração", descricao="Melhore sua atenção em 15 minutos", url="https://example.com/foco.mp3")
        ]
        db.session.add_all(meditacoes)
        db.session.commit()

init_routes(app)

if __name__ == '__main__':
    app.run(debug=True)