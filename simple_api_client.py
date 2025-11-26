import requests
import json
from typing import Optional, Dict, Any
import base64


class SimpleTheatreClient:
    def __init__(self):
        self.base_url = "https://barialibasov.pythonanywhere.com"
        self.session = requests.Session()
        # Добавляем заголовки для корректной работы с JSON
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.current_user = None

    def test_connection(self):
        """Тестирование подключения к серверу"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}

        except requests.exceptions.RequestException as e:
            return {"error": f"Connection failed: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response: {str(e)}\nResponse: {response.text}"}

    def login(self, username, password):
        """Авторизация пользователя"""
        try:
            data = {
                "username": username,
                "password": password
            }

            response = self.session.post(
                f"{self.base_url}/api/login",
                json=data,
                timeout=10
            )
            print(f"Login Status: {response.status_code}")
            print(f"Login Response: {response.text}")

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.current_user = result.get('user')
                    print(f"Current User: {self.current_user}")
                return result
            else:
                if "html" in response.text.lower():
                    return {"error": "Server error - check server logs"}
                return {"error": f"Login failed: {response.text}"}

        except requests.exceptions.RequestException as e:
            return {"error": f"Network error: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid response from server: {str(e)}\nResponse: {response.text}"}

    def register(self, username: str, password: str) -> bool:
        """Регистрация пользователя"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json={"username": username, "password": password}
            )
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False
        
    def get_participants(self):
        """Получение списка участников (не организаторов)"""
        try:
            response = requests.get(f"{self.base_url}/api/user/participants")
            return response.json()
        except requests.exceptions.RequestException:
            return []
        
    def get_current_user(self) -> Optional[Dict]:
        """Получение текущего пользователя через API"""
        try:
            # Делаем запрос к API без параметров - сервер сам определит текущего пользователя
            response = requests.get(f"{self.base_url}/api/auth/me")
            data = response.json()

            if data.get('success'):
                user_data = data.get('user')
                # Обновляем current_user если получили данные
                if user_data and not self.current_user:
                    self.current_user = user_data
                return user_data
            else:
                return None

        except requests.exceptions.RequestException as e:
            print(f"Ошибка получения текущего пользователя: {e}")
            # Возвращаем сохраненного пользователя как fallback
            return self.current_user

    # Методы для спектаклей
    def get_performances(self) -> list:
        try:
            response = requests.get(f"{self.base_url}/api/performances")
            return response.json()
        except requests.exceptions.RequestException:
            return []

    def get_performance(self, perf_id: int) -> Optional[Dict]:
        try:
            response = requests.get(f"{self.base_url}/api/performances/{perf_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException:
            return None

    def create_performance(self, title: str, description: str = "", performance_date: str = "",
                           cover_image: bytes = None) -> bool:
        try:
            cover_data = None
            if cover_image:
                cover_data = base64.b64encode(cover_image).decode('utf-8')

            response = requests.post(
                f"{self.base_url}/api/performances",
                json={
                    "title": title,
                    "description": description,
                    "performance_date": performance_date,
                    "cover_image": cover_data
                }
            )
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    def delete_performance(self, performance_id: int) -> Dict:
        """Удаление спектакля - возвращает полный ответ с предупреждениями"""
        try:
            response = requests.delete(f"{self.base_url}/api/performances/{performance_id}")
            data = response.json()
            return data  # Возвращаем полный ответ
        except requests.exceptions.RequestException:
            return {"success": False, "error": "Network error"}

    # Методы для ролей
    def get_roles(self, performance_id: int) -> list:
        try:
            response = requests.get(f"{self.base_url}/api/performances/{performance_id}/roles")
            return response.json()
        except requests.exceptions.RequestException:
            return []

    def create_role(self, performance_id: int, role_name: str, description: str = "") -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/api/roles",
                json={
                    "performance_id": performance_id,
                    "role_name": role_name,
                    "description": description
                }
            )
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    def delete_role(self, role_id: int) -> Dict:
        """Удаление роли - возвращает полный ответ с предупреждениями"""
        try:
            response = requests.delete(f"{self.base_url}/api/roles/{role_id}")
            data = response.json()
            return data  # Возвращаем полный ответ
        except requests.exceptions.RequestException:
            return {"success": False, "error": "Network error"}

    # Методы для заявок
    def apply_for_role(self, role_id: int) -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/api/apply",
                json={
                    "role_id": role_id,
                    "username": self.current_user['username'] if self.current_user else ""
                }
            )
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    def get_applications(self) -> list:
        try:
            username = self.current_user['username'] if self.current_user else ""
            role = self.current_user['role'] if self.current_user else "actor"
            response = requests.get(
                f"{self.base_url}/api/applications",
                params={"username": username, "role": role}
            )
            return response.json()
        except requests.exceptions.RequestException:
            return []

    def approve_application(self, application_id: int, applicant_username: str) -> bool:
        """Одобрение заявки - передаем username заявителя"""
        try:
            response = requests.post(
                f"{self.base_url}/api/applications/{application_id}/approve",
                json={
                    "username": applicant_username  # ← username того, кто подал заявку
                }
            )
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    def reject_application(self, application_id: int) -> bool:
        try:
            response = requests.post(f"{self.base_url}/api/applications/{application_id}/reject")
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    # Методы для занятий
    def get_lessons(self) -> list:
        try:
            response = requests.get(f"{self.base_url}/api/lessons")
            print(response.json())
            return response.json()
        except requests.exceptions.RequestException:
            return []

    def create_lesson(self, title: str, date: str, time: str = "", description: str = "", location: str = "") -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/api/lessons",
                json={
                    "title": title,
                    "date": date,
                    "time": time,
                    "description": description,
                    "location": location,
                    "created_by": self.current_user['username'] if self.current_user else ""
                }
            )
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    def delete_lesson(self, lesson_id: int) -> bool:
        try:
            response = requests.delete(f"{self.base_url}/api/lessons/{lesson_id}")
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    # Методы для файлов
    def get_files(self) -> list:
        try:
            response = requests.get(f"{self.base_url}/api/files")
            return response.json()
        except requests.exceptions.RequestException:
            return []

    def create_file(self, file_name: str, file_path: str, file_size: str = "", file_extension: str = "") -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/api/files",
                json={
                    "file_name": file_name,
                    "file_path": file_path,
                    "file_size": file_size,
                    "file_extension": file_extension,
                    "uploaded_by": self.current_user['username'] if self.current_user else ""
                }
            )
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    def delete_file(self, file_id: int) -> bool:
        try:
            response = requests.delete(f"{self.base_url}/api/files/{file_id}")
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    # Дополнительные методы
    def update_avatar(self, avatar_data: bytes) -> bool:
        """Обновление аватара пользователя"""
        try:
            avatar_base64 = base64.b64encode(avatar_data).decode('utf-8')
            response = requests.post(
                f"{self.base_url}/api/user/avatar",
                json={
                    "username": self.current_user['username'] if self.current_user else "",
                    "avatar": avatar_base64
                }
            )
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    def update_participation(self, is_part: bool) -> bool:
        """Обновление статуса участия текущего пользователя"""
        try:
            response = requests.post(
                f"{self.base_url}/api/user/participation",
                json={
                    "isPart": "Yes" if is_part else "No"
                }
            )
            data = response.json()
            print(data)
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    def get_participation(self, username: str = None) -> Optional[bool]:
        """Получение статуса участия"""
        try:
            # Определяем username
            if not username:
                if self.current_user and 'username' in self.current_user:
                    username = self.current_user['username']
                else:
                    print("No username provided and no current user")
                    return None

            print(f"Getting participation for username: {username}")

            response = requests.get(
                f"{self.base_url}/api/user/participation",
                params={"username": username},
                timeout=10
            )

            print(f"Participation response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Participation response data: {data}")

                if data.get('success'):
                    is_part = data.get('isPart')
                    print(f"Participation status: {is_part}")
                    return is_part == "Yes"
                else:
                    print(f"API error: {data.get('error')}")
                    return None
            else:
                print(f"HTTP error: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def get_organizers(self) -> list:
        """Получение списка организаторов"""
        try:
            response = requests.get(f"{self.base_url}/api/user/organizers")
            return response.json()

        except requests.exceptions.RequestException:
            return []

    def get_additional_files(self) -> list:
        """Получение дополнительных файлов"""
        try:
            response = requests.get(f"{self.base_url}/api/additional-files")
            return response.json()
        except requests.exceptions.RequestException:
            return []

    def create_additional_file(self, file_name: str, file_path: str, file_size: str = "", file_extension: str = "",
                               last_modified: str = "") -> bool:
        """Создание записи о дополнительном файле"""
        try:
            response = requests.post(
                f"{self.base_url}/api/additional-files",
                json={
                    "file_name": file_name,
                    "file_path": file_path,
                    "file_size": file_size,
                    "file_extension": file_extension,
                    "last_modified": last_modified
                }
            )
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    def delete_additional_file(self, file_path: str) -> bool:
        """Удаление дополнительного файла"""
        try:
            response = requests.delete(f"{self.base_url}/api/additional-files/{file_path}")
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException:
            return False

    def get_user_avatar(self, username: str = None) -> Optional[bytes]:
        """Получение аватара пользователя"""
        try:
            if not username:
                username = self.current_user['username'] if self.current_user else ""

            print(f"Requesting avatar for: {username}")

            response = requests.get(
                f"{self.base_url}/api/user/avatar",
                params={"username": username},
                timeout=10
            )

            print(f"Avatar response status: {response.status_code}")
            print(f"Avatar response headers: {response.headers}")

            if response.status_code == 200:
                try:
                    data = response.json()

                    if data.get('success'):
                        if data.get('avatar'):
                            print("Avatar found, decoding...")
                            return base64.b64decode(data['avatar'])
                        else:
                            print("No avatar in response")
                            return None
                    else:
                        print(f"API error: {data.get('error')}")
                        return None

                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Response text: {response.text}")
                    return None

            elif response.status_code == 500:
                print("Server error 500 - checking response...")
                print(f"Error response: {response.text}")
                return None
            else:
                print(f"Unexpected status code: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in get_user_avatar: {e}")
            return None


# Пример использования
if __name__ == "__main__":
    client = SimpleTheatreClient()

    # Тестирование подключения
    print("Testing connection...")
    result = client.test_connection()
    print(result)

    # Пример авторизации
    print("\nTesting login...")
    login_result = client.login("test_user", "test_password")
    print(login_result)

    if login_result.get('success'):
        # Получение спектаклей
        print("\nGetting performances...")
        performances = client.get_performances()
        print(f"Found {len(performances)} performances")

        # Получение уроков
        print("\nGetting lessons...")
        lessons = client.get_lessons()
        print(f"Found {len(lessons)} lessons")

        # Получение файлов
        print("\nGetting files...")
        files = client.get_files()
        print(f"Found {len(files)} files")