from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt
from datetime import datetime

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    sessoes = db.relationship('Sessao', backref='usuario', foreign_keys='Sessao.usuario_id')
    foruns = db.relationship('Forum', backref='usuario')
    postagens = db.relationship('Postagem', backref='usuario')
    mensagens_enviadas_como_usuario = db.relationship(
        'Mensagem',
        foreign_keys='Mensagem.usuario_remetente_id',
        backref='usuario_remetente'
    )
    mensagens_recebidas_como_usuario = db.relationship(
        'Mensagem',
        foreign_keys='Mensagem.usuario_destinatario_id',
        backref='usuario_destinatario'
    )

    def set_senha(self, senha):
        self.senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_senha(self, senha):
        return bcrypt.checkpw(senha.encode('utf-8'), self.senha_hash.encode('utf-8'))

class Profissional(UserMixin, db.Model):
    __tablename__ = 'profissional'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    especialidade = db.Column(db.String(100), nullable=False)
    aprovado = db.Column(db.Boolean, default=False)
    sessoes = db.relationship('Sessao', backref='profissional', foreign_keys='Sessao.profissional_id')
    mensagens_enviadas_como_profissional = db.relationship(
        'Mensagem',
        foreign_keys='Mensagem.profissional_remetente_id',
        backref='profissional_remetente'
    )
    mensagens_recebidas_como_profissional = db.relationship(
        'Mensagem',
        foreign_keys='Mensagem.profissional_destinatario_id',
        backref='profissional_destinatario'
    )

    def set_senha(self, senha):
        self.senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_senha(self, senha):
        return bcrypt.checkpw(senha.encode('utf-8'), self.senha_hash.encode('utf-8'))

class Administrador(UserMixin, db.Model):
    __tablename__ = 'administrador'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    nome = db.Column(db.String(100), nullable=True)

    def set_senha(self, senha):
        self.senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_senha(self, senha):
        return bcrypt.checkpw(senha.encode('utf-8'), self.senha_hash.encode('utf-8'))

class Sessao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)

class Forum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    postagens = db.relationship('Postagem', backref='forum')

class Postagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    forum_id = db.Column(db.Integer, db.ForeignKey('forum.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)

class Notificacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False)
    mensagem = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    lida = db.Column(db.Boolean, default=False)

class Mensagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_remetente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    profissional_remetente_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=True)
    usuario_destinatario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    profissional_destinatario_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=True)
    conteudo = db.Column(db.Text, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    lida = db.Column(db.Boolean, default=False)

class Meditacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(200), nullable=False)