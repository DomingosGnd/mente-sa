from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from models import db, Usuario, Profissional, Administrador, Sessao, Forum, Postagem, Notificacao, Mensagem, Meditacao
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def init_routes(app):
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('login.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            senha = request.form['senha']
            tipo = request.form.get('tipo', 'usuario')
            logger.debug(f"Tentativa de login: email={email}, tipo={tipo}")

            if tipo == 'usuario':
                user = Usuario.query.filter_by(email=email).first()
            elif tipo == 'profissional':
                user = Profissional.query.filter_by(email=email).first()
            else:
                user = Administrador.query.filter_by(email=email).first()

            if user:
                logger.debug(f"Usuário encontrado no banco: {user.email} ({user.__class__.__name__}, ID={user.id})")
                if user.check_senha(senha):
                    login_user(user)
                    session['user_type'] = user.__class__.__name__
                    session['_user_id'] = str(user.id)
                    logger.debug(f"Login bem-sucedido: {user.email} ({user.__class__.__name__}, ID={user.id})")
                    flash('Login realizado com sucesso!', 'success')
                    return redirect(url_for('dashboard'))
            flash('Email ou senha inválidos.', 'danger')
        return render_template('login.html')

    @app.route('/registro', methods=['GET', 'POST'])
    def registro():
        if request.method == 'POST':
            nome = request.form['nome']
            email = request.form['email']
            senha = request.form['senha']
            tipo = request.form.get('tipo', 'usuario')
            logger.debug(f"Tentativa de registro: email={email}, tipo={tipo}")

            if Usuario.query.filter_by(email=email).first() or \
               Profissional.query.filter_by(email=email).first() or \
               Administrador.query.filter_by(email=email).first():
                flash('Email já registrado.', 'danger')
                return redirect(url_for('registro'))

            if tipo == 'usuario':
                user = Usuario(nome=nome, email=email)
            elif tipo == 'profissional':
                user = Profissional(nome=nome, email=email, especialidade='Psicólogo')
            else:
                user = Administrador(email=email, nome=nome)

            user.set_senha(senha)
            db.session.add(user)
            db.session.commit()
            logger.debug(f"Usuário registrado: {user.email} ({user.__class__.__name__}, ID={user.id})")
            flash('Registro concluído! Faça login.', 'success')
            return redirect(url_for('login'))
        return render_template('registro.html')

    @app.route('/logout')
    @login_required
    def logout():
        logger.debug(f"Logout: {current_user.email} ({current_user.__class__.__name__}, ID={current_user.id})")
        session.pop('user_type', None)
        logout_user()
        flash('Você saiu da sua conta.', 'info')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        notificacoes = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).order_by(Notificacao.data.desc()).all()
        profissionais = Profissional.query.filter_by(aprovado=True).all()
        if current_user.__class__.__name__ == 'Usuario':
            return render_template('dashboard.html', notificacoes=notificacoes, profissionais=profissionais)
        elif current_user.__class__.__name__ == 'Profissional':
            sessoes = Sessao.query.filter_by(profissional_id=current_user.id).all()
            return render_template('dashboard.html', notificacoes=notificacoes, sessoes=sessoes)
        else:  # Administrador
            profissionais_pendentes = Profissional.query.filter_by(aprovado=False).all()
            return render_template('dashboard.html', notificacoes=notificacoes, profissionais_pendentes=profissionais_pendentes)

    @app.route('/agendar_sessao', methods=['POST'])
    @login_required
    def agendar_sessao():
        if current_user.__class__.__name__ != 'Usuario':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard'))
        profissional_id = request.form['profissional_id']
        data_hora = datetime.strptime(request.form['data_hora'], '%Y-%m-%dT%H:%M')
        sessao = Sessao(usuario_id=current_user.id, profissional_id=profissional_id, data_hora=data_hora)
        db.session.add(sessao)
        db.session.commit()
        notificacao_usuario = Notificacao(
            usuario_id=current_user.id,
            mensagem=f"Sessão agendada para {data_hora.strftime('%d/%m/%Y %H:%M')}",
            tipo='sessao',
            data=datetime.now()
        )
        notificacao_profissional = Notificacao(
            usuario_id=profissional_id,
            mensagem=f"Nova sessão agendada por {current_user.nome} para {data_hora.strftime('%d/%m/%Y %H:%M')}",
            tipo='sessao',
            data=datetime.now()
        )
        db.session.add_all([notificacao_usuario, notificacao_profissional])
        db.session.commit()
        flash('Sessão agendada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/forum', methods=['GET', 'POST'])
    @login_required
    def forum():
        if current_user.__class__.__name__ != 'Usuario':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            titulo = request.form['titulo']
            novo_forum = Forum(titulo=titulo, usuario_id=current_user.id)
            db.session.add(novo_forum)
            db.session.commit()
            notificacao = Notificacao(
                usuario_id=current_user.id,
                mensagem=f"Fórum '{titulo}' criado com sucesso!",
                tipo='forum',
                data=datetime.now()
            )
            db.session.add(notificacao)
            db.session.commit()
            flash('Fórum criado com sucesso!', 'success')
            return redirect(url_for('forum'))
        foruns = Forum.query.all()
        notificacoes = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).all()
        return render_template('forum.html', foruns=foruns, notificacoes=notificacoes)

    @app.route('/forum/<int:forum_id>', methods=['GET', 'POST'])
    @login_required
    def forum_detalhe(forum_id):
        if current_user.__class__.__name__ != 'Usuario':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard'))
        forum = Forum.query.get_or_404(forum_id)
        if request.method == 'POST':
            conteudo = request.form['conteudo']
            postagem = Postagem(conteudo=conteudo, forum_id=forum_id, usuario_id=current_user.id)
            db.session.add(postagem)
            db.session.commit()
            flash('Comentário adicionado!', 'success')
            return redirect(url_for('forum_detalhe', forum_id=forum_id))
        postagens = Postagem.query.filter_by(forum_id=forum_id).order_by(Postagem.data.asc()).all()
        notificacoes = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).all()
        return render_template('forum_detalhe.html', forum=forum, postagens=postagens, notificacoes=notificacoes)

    @app.route('/meditacoes')
    @login_required
    def meditacoes():
        if current_user.__class__.__name__ != 'Usuario':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard'))
        meditacoes = Meditacao.query.all()
        notificacoes = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).all()
        return render_template('meditacoes.html', meditacoes=meditacoes, notificacoes=notificacoes)

    @app.route('/chat/<int:usuario_id>', methods=['GET', 'POST'])
    @login_required
    def chat(usuario_id):
        if current_user.__class__.__name__ != 'Profissional':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard'))
        usuario = Usuario.query.get_or_404(usuario_id)
        if request.method == 'POST':
            conteudo = request.form['conteudo']
            mensagem = Mensagem(
                profissional_remetente_id=current_user.id,
                usuario_destinatario_id=usuario_id,
                conteudo=conteudo
            )
            db.session.add(mensagem)
            db.session.commit()
            flash('Mensagem enviada!', 'success')
            return redirect(url_for('chat', usuario_id=usuario_id))
        mensagens = Mensagem.query.filter(
            (
                (Mensagem.profissional_remetente_id == current_user.id) & 
                (Mensagem.usuario_destinatario_id == usuario_id)
            ) | (
                (Mensagem.usuario_remetente_id == usuario_id) & 
                (Mensagem.profissional_destinatario_id == current_user.id)
            )
        ).order_by(Mensagem.data.asc()).all()
        notificacoes = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).all()
        return render_template('chat.html', usuario=usuario, mensagens=mensagens, notificacoes=notificacoes)

    @app.route('/gerenciar_profissionais', methods=['GET', 'POST'])
    @login_required
    def gerenciar_profissionais():
        if current_user.__class__.__name__ != 'Administrador':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            profissional_id = request.form['profissional_id']
            acao = request.form['acao']
            profissional = Profissional.query.get_or_404(profissional_id)
            if acao == 'aprovar':
                profissional.aprovado = True
                db.session.commit()
                flash(f'Profissional {profissional.nome} aprovado!', 'success')
            elif acao == 'rejeitar':
                db.session.delete(profissional)
                db.session.commit()
                flash(f'Profissional {profissional.nome} rejeitado e removido!', 'success')
            return redirect(url_for('gerenciar_profissionais'))
        profissionais = Profissional.query.all()
        notificacoes = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).all()
        return render_template('gerenciar_profissionais.html', profissionais=profissionais, notificacoes=notificacoes)

    @app.route('/moderar_conteudo', methods=['GET', 'POST'])
    @login_required
    def moderar_conteudo():
        if current_user.__class__.__name__ != 'Administrador':
            flash('Acesso negado.', 'danger')
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            postagem_id = request.form['postagem_id']
            postagem = Postagem.query.get_or_404(postagem_id)
            db.session.delete(postagem)
            db.session.commit()
            flash('Postagem removida!', 'success')
            return redirect(url_for('moderar_conteudo'))
        foruns = Forum.query.all()
        notificacoes = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).all()
        return render_template('moderar_conteudo.html', foruns=foruns, notificacoes=notificacoes)

    @app.route('/marcar_notificacao_lida/<int:notificacao_id>', methods=['POST'])
    @login_required
    def marcar_notificacao_lida(notificacao_id):
        notificacao = Notificacao.query.get_or_404(notificacao_id)
        if notificacao.usuario_id == current_user.id:
            notificacao.lida = True
            db.session.commit()
        return redirect(url_for('dashboard'))