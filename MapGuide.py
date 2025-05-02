import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import requests


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Яндекс Карты")
        self.setGeometry(100, 100, 800, 600)
        self.latitude = 55.753995
        self.longitude = 37.621094
        self.zoom = 15
        self.map_type = "map"

        self.init_ui()

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.handle_map_response)

        self.update_map()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        control_layout = QHBoxLayout()

        self.coord_input = QLineEdit(f"{self.latitude}, {self.longitude}")
        self.coord_input.setPlaceholderText("Широта, долгота")
        control_layout.addWidget(self.coord_input)

        self.zoom_input = QLineEdit(str(self.zoom))
        self.zoom_input.setPlaceholderText("Масштаб (1-17)")
        control_layout.addWidget(self.zoom_input)

        self.search_btn = QPushButton("Поиск")
        self.search_btn.clicked.connect(self.update_map_by_coords)
        control_layout.addWidget(self.search_btn)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Введите адрес")
        control_layout.addWidget(self.address_input)

        self.address_btn = QPushButton("Найти адрес")
        self.address_btn.clicked.connect(self.search_by_address)
        control_layout.addWidget(self.address_btn)

        layout.addLayout(control_layout)
        self.map_label = QLabel()
        self.map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_label.setMinimumSize(600, 400)
        layout.addWidget(self.map_label)
        map_type_layout = QHBoxLayout()

        self.map_btn = QPushButton("Схема")
        self.map_btn.clicked.connect(lambda: self.set_map_type("map"))
        map_type_layout.addWidget(self.map_btn)

        self.sat_btn = QPushButton("Спутник")
        self.sat_btn.clicked.connect(lambda: self.set_map_type("sat"))
        map_type_layout.addWidget(self.sat_btn)

        self.hybrid_btn = QPushButton("Гибрид")
        self.hybrid_btn.clicked.connect(lambda: self.set_map_type("skl"))
        map_type_layout.addWidget(self.hybrid_btn)

        layout.addLayout(map_type_layout)

    def set_map_type(self, map_type):
        self.map_type = map_type
        self.update_map()

    def update_map(self):
        map_url = f"https://static-maps.yandex.ru/1.x/?ll={self.longitude},{self.latitude}&z={self.zoom}&l={self.map_type}&size=600,400"
        request = QNetworkRequest(QUrl(map_url))
        self.network_manager.get(request)

    def handle_map_response(self, reply):
        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                pixmap = QPixmap()
                pixmap.loadFromData(reply.readAll())
                if not pixmap.isNull():
                    self.map_label.setPixmap(pixmap)
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось загрузить карту")
            else:
                QMessageBox.warning(self, "Ошибка", f"Ошибка сети: {reply.errorString()}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
        finally:
            reply.deleteLater()

    def update_map_by_coords(self):
        try:
            coords = self.coord_input.text().split(",")
            if len(coords) == 2:
                self.latitude = float(coords[0].strip())
                self.longitude = float(coords[1].strip())

                zoom = self.zoom_input.text().strip()
                if zoom:
                    self.zoom = max(1, min(17, int(zoom)))
                    self.zoom_input.setText(str(self.zoom))

                self.update_map()
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректные координаты или масштаб")

    def search_by_address(self):
        address = self.address_input.text().strip()
        if not address:
            QMessageBox.warning(self, "Ошибка", "Введите адрес для поиска")
            return

        try:
            api_key = '40d1649f-0493-4b70-98ba-98533de7710b'
            url = f'http://geocode-maps.yandex.ru/1.x/?apikey={api_key}&geocode={address}&format=json'

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            toponym = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            coords = toponym["Point"]["pos"].split()

            self.longitude, self.latitude = map(float, coords)
            self.coord_input.setText(f"{self.latitude}, {self.longitude}")
            self.update_map()

        except requests.RequestException as e:
            QMessageBox.warning(self, "Ошибка сети", f"Не удалось выполнить запрос: {str(e)}")
        except (KeyError, IndexError):
            QMessageBox.warning(self, "Ошибка", "Адрес не найден")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        window = MapApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        sys.exit(1)