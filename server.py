from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import os
import base64
import json

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

# Абсолютный путь к базе данных для PythonAnywhere
DATABASE_PATH = '/home/BariAlibasov/theatre/theatre.db'


def get_db_connection():
    """Создание соединения с БД"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Инициализация базы данных"""
    conn = get_db_connection()

    # Создание таблиц, если их нет
    conn.execute('''
        CREATE TABLE IF NOT EXISTS performances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            performance_date TEXT,
            cover_image BLOB
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            performance_id INTEGER,
            role_name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'open',
            assigned_user TEXT,
            FOREIGN KEY (performance_id) REFERENCES performances (id)
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS role_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER,
            username TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles (id)
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT,
            isCurrent TEXT DEFAULT 'no',
            isPart TEXT DEFAULT 'No',
            avatar BLOB
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT,
            time TEXT,
            description TEXT,
            location TEXT,
            created_by TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT,
            file_size TEXT,
            file_extension TEXT,
            uploaded_by TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS additional_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT,
            file_size TEXT,
            file_extension TEXT,
            last_modified TIMESTAMP,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


# Инициализируем БД при старте
init_database()


# API endpoints
@app.route('/')
def home():
    return jsonify({"message": "Theatre Server is running", "status": "ok"})


@app.route('/api/login', methods=['POST'])
def login():
    """Авторизация пользователя с проверкой пароля"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password are required"}), 400

    conn = get_db_connection()

    try:
        # Ищем пользователя в базе с проверкой пароля
        user = conn.execute(
            'SELECT username, role, password FROM user WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()

        if user:
            # Устанавливаем пользователя как текущего
            conn.execute('UPDATE user SET isCurrent = "no"')
            conn.execute('UPDATE user SET isCurrent = "yes" WHERE username = ?', (username,))

            # Проверяем специальный пароль для организатора
            if password.endswith("20041889"):
                conn.execute('UPDATE user SET role = "organizer" WHERE username = ?', (username,))

            conn.commit()

            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": {
                    "username": user['username'],
                    "role": user['role']
                }
            })
        else:
            return jsonify({"success": False, "error": "Invalid username or password"}), 401

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500
    finally:
        conn.close()


@app.route('/api/auth/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password are required"}), 400

    conn = get_db_connection()

    try:
        # Проверяем, не существует ли уже пользователь
        existing_user = conn.execute(
            'SELECT username FROM user WHERE username = ?', (username,)
        ).fetchone()

        if existing_user:
            return jsonify({"success": False, "error": "User already exists"}), 400

        # Создаем нового пользователя (по умолчанию actor)
        conn.execute(
            'INSERT INTO user (username, password, role, isCurrent) VALUES (?, ?, "actor", "no")',
            (username, password)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "User registered successfully"
        })

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500
    finally:
        conn.close()


@app.route('/api/auth/me', methods=['GET'])
def get_current_user_api():
    """Получение текущего пользователя"""
    username = request.args.get('username')

    conn = get_db_connection()

    try:
        if username:
            user = conn.execute(
                'SELECT username, role FROM user WHERE username = ?', (username,)
            ).fetchone()
        else:
            # Ищем текущего пользователя
            user = conn.execute(
                'SELECT username, role FROM user WHERE isCurrent = "yes"'
            ).fetchone()

        if user:
            return jsonify({
                "success": True,
                "user": {
                    "username": user['username'],
                    "role": user['role']
                }
            })
        else:
            return jsonify({"success": False, "error": "No user found"}), 404

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500
    finally:
        conn.close()


# ==================== УРОКИ ====================

@app.route('/api/lessons', methods=['GET'])
def get_lessons():
    """Получение списка уроков"""
    conn = get_db_connection()

    try:
        lessons = conn.execute(
            'SELECT id, title, date, time, description, location, created_by FROM lessons ORDER BY date, time'
        ).fetchall()
        return jsonify([dict(lesson) for lesson in lessons])
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()


@app.route('/api/lessons', methods=['POST'])
def create_lesson():
    """Создание урока"""
    data = request.json
    title = data.get('title')
    date = data.get('date')
    time = data.get('time', '')
    description = data.get('description', '')
    location = data.get('location', '')
    created_by = data.get('created_by', '')

    if not title or not date:
        return jsonify({"success": False, "error": "Title and date are required"}), 400

    conn = get_db_connection()

    try:
        conn.execute(
            'INSERT INTO lessons (title, date, time, description, location, created_by) VALUES (?, ?, ?, ?, ?, ?)',
            (title, date, time, description, location, created_by)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Lesson created successfully"})

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500
    finally:
        conn.close()


@app.route('/api/lessons/<int:lesson_id>', methods=['DELETE'])
def delete_lesson(lesson_id):
    """Удаление урока"""
    conn = get_db_connection()

    try:
        conn.execute('DELETE FROM lessons WHERE id = ?', (lesson_id,))
        conn.commit()

        return jsonify({"success": True, "message": "Lesson deleted successfully"})

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500
    finally:
        conn.close()


# ==================== СПЕКТАКЛИ ====================

@app.route('/api/performances', methods=['GET'])
def get_performances():
    """Получение списка спектаклей"""
    conn = get_db_connection()
    performances = conn.execute(
        'SELECT id, title, performance_date FROM performances ORDER BY performance_date'
    ).fetchall()
    conn.close()

    return jsonify([dict(perf) for perf in performances])


@app.route('/api/performances/<int:perf_id>', methods=['GET'])
def get_performance(perf_id):
    """Получение деталей спектакля"""
    conn = get_db_connection()
    performance = conn.execute(
        'SELECT * FROM performances WHERE id = ?', (perf_id,)
    ).fetchone()
    conn.close()

    if performance:
        return jsonify(dict(performance))
    else:
        return jsonify({"error": "Performance not found"}), 404


@app.route('/api/performances', methods=['POST'])
def add_performance():
    """Добавление спектакля"""
    data = request.json
    title = data.get('title')
    description = data.get('description', '')
    performance_date = data.get('performance_date', '')
    cover_image = data.get('cover_image')  # base64 encoded image

    if not title:
        return jsonify({"success": False, "error": "Title is required"}), 400

    conn = get_db_connection()

    try:
        conn.execute(
            'INSERT INTO performances (title, description, performance_date, cover_image) VALUES (?, ?, ?, ?)',
            (title, description, performance_date, cover_image)
        )
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Спектакль добавлен!"})
    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500


@app.route('/api/performances/<int:perf_id>', methods=['DELETE'])
def delete_performance(perf_id):
    """Удаление спектакля с подтверждением если есть назначенные роли"""
    conn = get_db_connection()

    try:
        # Проверяем есть ли назначенные роли
        assigned_roles = conn.execute(
            'SELECT COUNT(*) FROM roles WHERE performance_id = ? AND assigned_user IS NOT NULL',
            (perf_id,)
        ).fetchone()[0]

        # Получаем информацию о спектакле для сообщения
        perf_info = conn.execute(
            'SELECT title FROM performances WHERE id = ?', (perf_id,)
        ).fetchone()

        if not perf_info:
            return jsonify({"success": False, "error": "Спектакль не найден"}), 404

        perf_title = perf_info['title']

        # УДАЛЯЕМ спектакль даже если есть назначенные роли (каскадное удаление)
        conn.execute('DELETE FROM performances WHERE id = ?', (perf_id,))
        conn.commit()
        conn.close()

        # Возвращаем предупреждение если были назначенные роли
        if assigned_roles > 0:
            return jsonify({
                "success": True,
                "message": "Спектакль удален",
                "warning": f"Спектакль '{perf_title}' удален вместе с {assigned_roles} назначенными ролями"
            })
        else:
            return jsonify({
                "success": True,
                "message": "Спектакль удален"
            })

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500


# ==================== РОЛИ ====================

@app.route('/api/performances/<int:perf_id>/roles', methods=['GET'])
def get_roles(perf_id):
    """Получение ролей для спектакля"""
    conn = get_db_connection()
    roles = conn.execute(
        'SELECT id, role_name, description, status, assigned_user FROM roles WHERE performance_id = ? ORDER BY role_name',
        (perf_id,)
    ).fetchall()
    conn.close()

    return jsonify([dict(role) for role in roles])


@app.route('/api/roles', methods=['POST'])
def add_role():
    """Добавление роли"""
    data = request.json
    performance_id = data.get('performance_id')
    role_name = data.get('role_name')
    description = data.get('description', '')

    if not performance_id or not role_name:
        return jsonify({"success": False, "error": "Performance ID and role name are required"}), 400

    conn = get_db_connection()

    try:
        conn.execute(
            'INSERT INTO roles (performance_id, role_name, description) VALUES (?, ?, ?)',
            (performance_id, role_name, description)
        )
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Роль добавлена!"})
    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500


@app.route('/api/roles/<int:role_id>', methods=['DELETE'])
def delete_role(role_id):
    """Удаление роли с подтверждением если она назначена"""
    conn = get_db_connection()

    try:
        # Проверяем назначена ли роль
        role_info = conn.execute(
            'SELECT role_name, assigned_user FROM roles WHERE id = ?', (role_id,)
        ).fetchone()

        if not role_info:
            return jsonify({"success": False, "error": "Роль не найдена"}), 404

        role_name = role_info['role_name']
        assigned_user = role_info['assigned_user']

        # Если роль назначена - возвращаем предупреждение, но не блокируем удаление
        if assigned_user:
            # УДАЛЯЕМ роль даже если она назначена (каскадное удаление заявок)
            conn.execute('DELETE FROM roles WHERE id = ?', (role_id,))
            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "message": "Роль удалена",
                "warning": f"Роль '{role_name}' была назначена пользователю: {assigned_user}, но была удалена"
            })
        else:
            # Роль не назначена - просто удаляем
            conn.execute('DELETE FROM roles WHERE id = ?', (role_id,))
            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "message": "Роль удалена"
            })

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500


# ==================== ЗАЯВКИ ====================

@app.route('/api/applications', methods=['GET'])
def get_applications():
    """Получение заявок"""
    username = request.args.get('username')
    user_role = request.args.get('role')

    conn = get_db_connection()

    try:
        if user_role == 'organizer':
            applications = conn.execute('''
                SELECT ra.id, r.role_name, p.title, ra.username, ra.applied_at, ra.status
                FROM role_applications ra
                JOIN roles r ON ra.role_id = r.id
                JOIN performances p ON r.performance_id = p.id
                ORDER BY ra.applied_at
            ''').fetchall()
        else:
            applications = conn.execute('''
                SELECT ra.id, r.role_name, p.title, ra.status, ra.applied_at
                FROM role_applications ra
                JOIN roles r ON ra.role_id = r.id
                JOIN performances p ON r.performance_id = p.id
                WHERE ra.username = ? ORDER BY ra.applied_at
            ''', (username,)).fetchall()

        conn.close()
        return jsonify([dict(app) for app in applications])
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@app.route('/api/apply', methods=['POST'])
def apply_for_role():
    """Подача заявки на роль"""
    data = request.json
    role_id = data.get('role_id')
    username = data.get('username')

    if not role_id or not username:
        return jsonify({"success": False, "error": "Role ID and username are required"}), 400

    conn = get_db_connection()

    try:
        # Проверка существующей заявки
        existing = conn.execute(
            'SELECT 1 FROM role_applications WHERE role_id = ? AND username = ?',
            (role_id, username)
        ).fetchone()

        if existing:
            return jsonify({"success": False, "error": "Вы уже подавали заявку на эту роль"}), 400

        # Создание заявки
        conn.execute(
            'INSERT INTO role_applications (role_id, username) VALUES (?, ?)',
            (role_id, username)
        )
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Заявка подана!"})
    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500


@app.route('/api/applications/<int:app_id>/approve', methods=['POST'])
def approve_application(app_id):
    """Одобрение заявки с последующим удалением"""
    data = request.json
    username = data.get('username')

    conn = get_db_connection()

    try:
        application = conn.execute(
            'SELECT role_id FROM role_applications WHERE id = ?', (app_id,)
        ).fetchone()

        if not application:
            return jsonify({"success": False, "error": "Заявка не найдена"}), 404

        role_id = application['role_id']

        conn.execute(
            'UPDATE roles SET status = "assigned", assigned_user = ? WHERE id = ?',
            (username, role_id)
        )

        # УДАЛЯЕМ заявку после одобрения
        conn.execute('DELETE FROM role_applications WHERE id = ?', (app_id,))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Заявка одобрена и удалена!"})
    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500


@app.route('/api/user/avatar', methods=['GET'])
def get_user_avatar():
    """Получение аватара пользователя"""
    username = request.args.get('username')
    print(f"GET AVATAR - Username: {username}")

    if not username:
        return jsonify({"success": False, "error": "Username is required"}), 400

    conn = get_db_connection()

    try:
        result = conn.execute(
            'SELECT avatar FROM user WHERE username = ?', (username,)
        ).fetchone()

        print(f"Database result type: {type(result['avatar']) if result and result['avatar'] else 'None'}")
        print(f"Database result length: {len(result['avatar']) if result and result['avatar'] else 0}")

        conn.close()

        if result and result['avatar']:
            avatar_data = result['avatar']

            # Проверяем тип данных
            if isinstance(avatar_data, bytes):
                # Если это байты - кодируем в base64
                print("Avatar is bytes, encoding to base64...")
                avatar_base64 = base64.b64encode(avatar_data).decode('utf-8')
            elif isinstance(avatar_data, str):
                # Если это уже строка (возможно уже base64) - возвращаем как есть
                print("Avatar is string, returning as is...")
                avatar_base64 = avatar_data
            else:
                print(f"Unknown avatar type: {type(avatar_data)}")
                return jsonify({"success": True, "avatar": None})

            print("Avatar processed successfully")
            return jsonify({
                "success": True,
                "avatar": avatar_base64
            })
        else:
            print("No avatar found")
            return jsonify({"success": True, "avatar": None})

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"success": False, "error": f"Unexpected error: {e}"}), 500




@app.route('/api/applications/<int:app_id>/reject', methods=['POST'])
def reject_application(app_id):
    """Отклонение заявки"""
    conn = get_db_connection()

    try:
        # ПРОСТО УДАЛЯЕМ заявку при отклонении
        conn.execute('DELETE FROM role_applications WHERE id = ?', (app_id,))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Заявка отклонена"})
    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500


# ==================== ФАЙЛЫ ====================

@app.route('/api/files', methods=['GET'])
def get_files():
    """Получение списка файлов"""
    conn = get_db_connection()

    try:
        files = conn.execute(
            'SELECT id, file_name, file_path, file_size, file_extension, uploaded_by, uploaded_at FROM files ORDER BY uploaded_at DESC'
        ).fetchall()
        return jsonify([dict(file) for file in files])
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()


@app.route('/api/files', methods=['POST'])
def create_file():
    """Создание записи о файле"""
    data = request.json
    file_name = data.get('file_name')
    file_path = data.get('file_path', '')
    file_size = data.get('file_size', '')
    file_extension = data.get('file_extension', '')
    uploaded_by = data.get('uploaded_by', '')

    if not file_name:
        return jsonify({"success": False, "error": "File name is required"}), 400

    conn = get_db_connection()

    try:
        conn.execute(
            'INSERT INTO files (file_name, file_path, file_size, file_extension, uploaded_by) VALUES (?, ?, ?, ?, ?)',
            (file_name, file_path, file_size, file_extension, uploaded_by)
        )
        conn.commit()

        return jsonify({"success": True, "message": "File record created successfully"})

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500
    finally:
        conn.close()


@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Удаление записи о файле"""
    conn = get_db_connection()

    try:
        conn.execute('DELETE FROM files WHERE id = ?', (file_id,))
        conn.commit()

        return jsonify({"success": True, "message": "File record deleted successfully"})

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500
    finally:
        conn.close()


# ==================== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ====================

@app.route('/api/user/avatar', methods=['POST'])
def update_avatar():
    """Обновление аватара пользователя"""
    data = request.json
    username = data.get('username')
    avatar_data = data.get('avatar')  # base64 encoded image

    if not username:
        return jsonify({"success": False, "error": "Username is required"}), 400

    conn = get_db_connection()

    try:
        conn.execute(
            'UPDATE user SET avatar = ? WHERE username = ?',
            (avatar_data, username)
        )
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Avatar updated successfully"})
    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500


@app.route('/api/user/participation', methods=['GET'])
def get_participation():
    """Получение статуса участия текущего пользователя"""
    conn = get_db_connection()

    try:
        # Ищем текущего пользователя
        result = conn.execute(
            'SELECT username, isPart FROM user WHERE isCurrent = "yes"'
        ).fetchone()

        conn.close()

        if result:
            username = result['username']
            is_part = result['isPart']
            print(f"Found participation status: {is_part} for current user: {username}")
            return jsonify({
                "success": True,
                "isPart": is_part,
                "username": username
            })
        else:
            print("No current user found")
            return jsonify({
                "success": False,
                "error": "No current user found"
            }), 404

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500

@app.route('/api/user/participation', methods=['POST'])
def update_participation():
    """Обновление статуса участия текущего пользователя"""
    data = request.json
    is_part = data.get('isPart', 'No')

    conn = get_db_connection()

    try:
        # Ищем текущего пользователя
        current_user = conn.execute(
            'SELECT username FROM user WHERE isCurrent = "yes"'
        ).fetchone()

        if not current_user:
            return jsonify({"success": False, "error": "No current user found"}), 404

        username = current_user['username']

        conn.execute(
            'UPDATE user SET isPart = ? WHERE username = ?',
            (is_part, username)
        )
        conn.commit()
        conn.close()

        print(f"Updated participation to {is_part} for current user: {username}")
        return jsonify({
            "success": True,
            "message": "Participation status updated",
            "username": username
        })
    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500


@app.route('/api/user/organizers', methods=['GET'])
def get_organizers():
    """Получение списка организаторов"""
    conn = get_db_connection()

    try:
        organizers = conn.execute(
            'SELECT username, avatar FROM user WHERE isPart = "Yes" AND role = "organizer"'
        ).fetchall()
        conn.close()

        return jsonify([dict(org) for org in organizers])
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@app.route('/api/additional-files', methods=['GET'])
def get_additional_files():
    """Получение дополнительных файлов"""
    conn = get_db_connection()

    try:
        files = conn.execute(
            'SELECT file_name, file_path, file_size, file_extension, last_modified FROM additional_files ORDER BY created_date DESC'
        ).fetchall()
        return jsonify([dict(file) for file in files])
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()


@app.route('/api/additional-files', methods=['POST'])
def create_additional_file():
    """Создание записи о дополнительном файле"""
    data = request.json
    file_name = data.get('file_name')
    file_path = data.get('file_path', '')
    file_size = data.get('file_size', '')
    file_extension = data.get('file_extension', '')
    last_modified = data.get('last_modified', '')

    if not file_name:
        return jsonify({"success": False, "error": "File name is required"}), 400

    conn = get_db_connection()

    try:
        conn.execute(
            'INSERT INTO additional_files (file_name, file_path, file_size, file_extension, last_modified) VALUES (?, ?, ?, ?, ?)',
            (file_name, file_path, file_size, file_extension, last_modified)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Additional file record created successfully"})

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500
    finally:
        conn.close()


@app.route('/api/additional-files/<path:file_path>', methods=['DELETE'])
def delete_additional_file(file_path):
    """Удаление записи о дополнительном файле"""
    conn = get_db_connection()

    try:
        conn.execute('DELETE FROM additional_files WHERE file_path = ?', (file_path,))
        conn.commit()

        return jsonify({"success": True, "message": "Additional file record deleted successfully"})

    except sqlite3.Error as e:
        return jsonify({"success": False, "error": f"Database error: {e}"}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)