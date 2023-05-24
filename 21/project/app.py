from flask import Flask, jsonify, request, render_template, redirect, flash, url_for, session
from flask_sqlalchemy import SQLAlchemy
import hashlib
import string
import random

app = Flask(__name__)
app.template_folder = 'C:\\Users\\AloneWasser\\Desktop\\21\\templates'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\AloneWasser\\Desktop\\21\\instance\\data.db'
UPLOAD_FOLDER = 'C:\\Users\\AloneWasser\\Desktop\\21\\'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER




from project.models import *




db = SQLAlchemy(app)
with app.app_context():
    db.create_all()


def check_admin_status(token):
    user = User.query.filter_by(token=token).first()
    if user and user.is_admin:
        return True
    return False

# ...

# Функция для создания администратора по умолчанию
def create_default_admin():
    default_admin_username = 'admin'
    default_admin_password = 'adminpassword'

    admin = User.query.filter_by(username=default_admin_username, is_admin=True).first()
    if admin is None:
        hashed_password = hash_password(default_admin_password)
        admin = User(username=default_admin_username, password=hashed_password, is_admin=True)
        db.session.add(admin)
        db.session.commit()

# Вспомогательная функция для хеширования пароля
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Вспомогательная функция для проверки пароля
def check_password(password, hashed_password):
    return hashlib.sha256(password.encode()).hexdigest() == hashed_password




def generate_token(token_type):
    if token_type == 'admin':
        admin_token = 'admin_token'  # Админский токен
        hashed_token = hashlib.sha256(admin_token.encode('utf-8')).hexdigest()  # Хеширование админского токена
    else:
        user_token = 'user_token'  # Пользовательский токен
        hashed_token = hashlib.sha256(user_token.encode('utf-8')).hexdigest()  # Хеширование пользовательского токена

    return hashed_token


@app.before_request
def setup():

    # Вызов функции для создания администратора по умолчанию
    create_default_admin()



@app.route('/')
def home():
    token = session.get('token')  # Получение токена из сеанса пользователя
    return render_template('index.html', token=token)
    print("Flask app error:", e)


# Роут для страницы с информацией о конкретном курсе
@app.route('/courses/<int:course_id>')
def course_details(course_id):
    token = request.headers.get('Authorization')
    session['token'] = token  # Сохранение токена в сеансе
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    tests = Test.query.filter_by(course_id=course_id).all()
    return render_template('course_details.html', course=course, tests=tests,
                           token=request.headers.get('Authorization'))




# Роут для страницы с созданием курса
@app.route('/create_course', methods=['POST', 'GET'])
def create_course():
    token = session.get('token')
    username = session.get('username')

    if not token:
        return redirect('/login')

    is_admin_token = (token == generate_token('admin'))  # Проверяем, является ли токен админским

    if not is_admin_token:
        return redirect('/courses')  # Redirect regular users to the "Courses" page

    courses = Course.query.all()

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        if not title or not description:
            return jsonify({'error': 'Missing data'}), 400

        course = Course(title=title, description=description)
        db.session.add(course)
        db.session.commit()

        return redirect('/courses')

    return render_template('create_course.html')



# Роут для страницы с созданием теста
@app.route('/courses/<int:course_id>/add_test', methods=['POST'])
def add_test(course_id):
    token = session.get('token')
    username = session.get('username')

    if not token:
        return redirect('/login')

    is_admin_token = (token == generate_token('admin'))  # Проверяем, является ли токен админским

    if not is_admin_token:
        return jsonify({'error': 'Unauthorized'}), 401

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    # Получаем данные из POST-запроса
    question_count = request.form.get('question_count')  # Количество вопросов
    pass_percentage = request.form.get('pass_percentage')  # Процент успешно пройденных вопросов
    correct_answers = request.form.getlist('correct_answers')  # Правильные ответы в вопросах

    # Создаем новый тест
    test = Test(course_id=course_id, question_count=question_count, pass_percentage=pass_percentage)
    db.session.add(test)
    db.session.commit()

    # Сохраняем правильные ответы вопросов
    for question_id, correct_answer in enumerate(correct_answers, start=1):
        question = TestQuestion(test_id=test.id, question_id=question_id, correct_answer=correct_answer)
        db.session.add(question)

    db.session.commit()

    return redirect('/courses')



@app.route('/courses/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    token = session.get('token')
    username = session.get('username')

    if not token:
        return redirect('/login')

    is_admin_token = (token == generate_token('admin'))  # Проверяем, является ли токен админским

    if not is_admin_token:
        return jsonify({'error': 'Unauthorized'}), 401

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    db.session.delete(course)
    db.session.commit()

    return redirect('/courses')



# ...
# Определение функции secure_filename
def secure_filename(filename):
    # Допустимые символы для имени файла
    allowed_chars = string.ascii_letters + string.digits + '._-'

    # Удаляем символы, отличные от допустимых
    cleaned_filename = ''.join(c for c in filename if c in allowed_chars)

    # Генерируем случайное имя файла, если после очистки имя стало пустым
    if not cleaned_filename:
        random_chars = ''.join(random.choices(allowed_chars, k=8))
        cleaned_filename = f'unnamed_{random_chars}'

    return cleaned_filename

# ...
# Функция проверки допустимых расширений файлов
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#
# @app.route('/upload_avatar', methods=['POST'])
# def upload_avatar():
#     if 'avatar' not in request.files:
#         return 'No file uploaded', 400
#
#     avatar = request.files['avatar']
#
#     if avatar.filename == '':
#         return 'No selected file', 400
#
#     if avatar and allowed_file(avatar.filename):
#         filename = secure_filename(avatar.filename)  # Используем безопасное имя файла
#         avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Сохранение файла аватара
#     else:
#         filename = 'default_avatar.png'  # Используйте дефолтный аватар, если файл не был загружен

    return 'File uploaded successfully'

# ...
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        # Проверка наличия активной сессии пользователя
        if 'username' in session:
            return redirect(url_for('courses'))

        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        avatar = request.files['avatar']  # Получение файла аватара из формы

        user = User.query.filter_by(username=username).first()

        if user:
            error_message = 'Имя пользователя уже существует'
            return render_template('register.html', error_message=error_message)

        if password != confirm_password:
            error_message = 'Пароли не совпадают'
            return render_template('register.html', error_message=error_message)

            # Проверка загрузки файла аватара
            if avatar and allowed_file(avatar.filename):
                filename = secure_filename(avatar.filename)  # Используем безопасное имя файла
                avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Сохранение файла аватара
            else:
                filename = 'default_avatar.png'  # Используйте дефолтный аватар, если файл не был загружен

        # Создание нового пользователя
        token = generate_token()
        new_user = User(username=username, password=hash_password(password), token=token, avatar=filename)
        db.session.add(new_user)
        db.session.commit()

        # Успешная регистрация
        flash('Регистрация прошла успешно', 'success')
        return redirect(url_for('courses'))

    return render_template('register.html')




# ...

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        if 'username' in session:
            return redirect(url_for('courses'))

        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if not user or not check_password(password, user.password):
            error_message = 'Неверное имя пользователя или пароль'
            return render_template('login.html', error_message=error_message)

        if user.is_admin:
            token_type = 'admin'
        else:
            token_type = 'user'

        token = generate_token(token_type)

        session['username'] = username
        session['token'] = token
        print(f"Token saved in session: {session['token']}")
        if token_type == 'admin':
            print("Admin token is set")  # Проверка задания админского токена

        flash('Вход выполнен успешно', 'success')
        return redirect(url_for('courses'))

    return render_template('login.html')




# ...

@app.route('/courses')
def courses():
    token = session.get('token')
    username = session.get('username')

    if not token:
        return redirect('/login')

    is_admin_token = (token == generate_token('admin'))  # Проверяем, является ли токен админским

    courses = Course.query.all()

    return render_template('courses.html', courses=courses, username=username, is_admin_token=is_admin_token)









# ...

@app.route('/logout', methods=['POST'])
def logout():
    # Проверка наличия активной сессии пользователя
    if 'username' in session:
        session.pop('username')
        session.pop('token', None)  # Удаление токена из сеанса

    return render_template('login.html')


# ...


# ...

if __name__ == '__main__':
    app.secret_key = 'your_secret_key_here'
    app.run(debug=True)

