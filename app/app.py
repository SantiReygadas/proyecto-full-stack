from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'llavesecreta' 

# Configuracion base de datos PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:contraseña$@localhost/full-stack'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Clases para tablas en la base de datos
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    answers = db.relationship('Answer', back_populates='user')
    questions = db.relationship('Question', back_populates='user')

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    answers = db.relationship('Answer', back_populates='question', cascade='all, delete-orphan')
    
    user = db.relationship('User', back_populates='questions')


class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.String(1000), nullable=False)

    question = db.relationship('Question', back_populates='answers')
    user = db.relationship('User', back_populates='answers')



# Rutas
@app.route('/responder/<int:question_id>', methods=['GET', 'POST'])
def responder(question_id):
    if 'user_id' in session:
        if request.method == 'POST':
            content = request.form['content']
            user_id = int(session['user_id'])
            new_answer = Answer(question_id=question_id, user_id=user_id, content=content)
            db.session.add(new_answer)
            db.session.commit()
            return redirect(url_for('ver_pregunta', question_id=question_id))
        return render_template('responder.html', question=Question.query.get_or_404(question_id), user=session.get('user_id'))
    else:
        flash('Debes iniciar sesión para responder.', 'warning')
        return redirect(url_for('login'))
    
    
@app.route('/eliminar_pregunta/<int:question_id>', methods=['POST'])
def eliminar_pregunta(question_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para eliminar una pregunta.', 'warning')
        return redirect(url_for('login'))

    question = Question.query.get_or_404(question_id)

    if question.user_id != session['user_id']:
        flash('No tienes permiso para eliminar esta pregunta.', 'danger')
        return redirect(url_for('ver_pregunta', question_id=question_id))
    
    for answer in question.answers:
        db.session.delete(answer)

    db.session.delete(question)
    db.session.commit()
    flash('Pregunta eliminada correctamente.', 'success')
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        questions = Question.query.all()
        return render_template('index.html', user=session.get('user_id'), questions=questions)
    else:
        questions = Question.query.all()
        return render_template('index.html', questions=questions)
    

@app.route('/pregunta', methods=['GET', 'POST'])
def preguntar():
    if 'user_id' in session:
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            user_id = session['user_id']
            new_question = Question(title=title, description=description, user_id=user_id)
            db.session.add(new_question)
            db.session.commit()
            return redirect(url_for('index'))
        return render_template('pregunta.html', user=session.get('user_id'))
    else:
        flash('Debes iniciar sesión para acceder a esta página.', 'warning')
        return redirect(url_for('login'))
    

@app.route('/ver_pregunta/<int:question_id>', methods=['GET'])
def ver_pregunta(question_id):  
    question = Question.query.get_or_404(question_id)
    return render_template('ver_pregunta.html', question=question, user=session.get('user_id'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('index'))
        flash('Nombre de usuario o contraseña incorrectos.', 'danger')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya está en uso.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Sesión cerrada exitosamente.', 'success')
    return redirect(url_for('index'))



#-----------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
