import os
import json
import requests
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivy.uix.scrollview import ScrollView
from kivymd.uix.snackbar import Snackbar
import pyrebase4

# Firebase config
firebase_config = {
    "apiKey": "AIzaSyCBNE1-04xpDNBGvo-wqypfcHln0vZDX0s",
    "authDomain": "wellbeingtracker-537ec.firebaseapp.com",
    "projectId": "wellbeingtracker-537ec",
    "storageBucket": "wellbeingtracker-537ec.appspot.com",
    "messagingSenderId": "308895666340",
    "appId": "1:308895666340:web:7e4b4a92f2ba707fd35631",
    "databaseURL": "https://wellbeingtracker-537ec-default-rtdb.asia-southeast1.firebasedatabase.app"
}

BACKEND_URL = "http://localhost:8000"

class WellbeingApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        self.file_path = os.path.join(os.path.dirname(__file__), "tasks.txt")
        self.nav = MDBottomNavigation()
        
        # Firebase init
        try:
            self.firebase = pyrebase4.initialize_app(firebase_config)
            self.auth = self.firebase.auth()
        except:
            self.firebase = None
            self.auth = None

        # HALAMAN LOGIN
        self.item_login = MDBottomNavigationItem(name='screen 1', text='Login', icon='account-circle')
        login_layout = MDBoxLayout(orientation='vertical', padding=30, spacing=20)
        login_layout.add_widget(MDLabel(text="WELLBEING LOGIN", halign="center", font_style="H5", bold=True))

        self.email_input = MDTextField(text="aqib14046@gmail.com", hint_text="Email", mode="rectangle")
        self.password_input = MDTextField(text="Sib9otallah!", hint_text="Password", mode="rectangle", password=True)
        btn_login = MDRaisedButton(text="MASUK", pos_hint={"center_x": .5}, on_release=self.proses_login)

        login_layout.add_widget(self.email_input)
        login_layout.add_widget(self.password_input)
        login_layout.add_widget(btn_login)
        self.item_login.add_widget(login_layout)
        self.nav.add_widget(self.item_login)

        return self.nav

    def proses_login(self, instance):
        """Login ke Firebase dan backend"""
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        
        try:
            # Firebase login
            user = self.auth.sign_in_with_email_and_password(email, password)
            self.user_token = user['idToken']
            self.firebase_uid = user['localId']
            
            # Backend login (verify token)
            resp = requests.post(
                f"{BACKEND_URL}/login",
                params={"token": self.user_token},
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                self.user_id = data.get('user_id')
                print(f"Login Berhasil! User ID: {self.user_id}, Firebase UID: {self.firebase_uid}")
                self.buat_halaman_jurnal()
                Clock.schedule_once(self.pindah_halaman, 0.2)
            else:
                Snackbar(text="Backend error!").open()
        except Exception as e:
            print(f"Login error: {e}")
            Snackbar(text="Login gagal!").open()

    def pindah_halaman(self, dt):
        self.nav.switch_tab('screen 2')
        Clock.schedule_once(lambda x: self.nav.remove_widget(self.item_login), 0.1)

    def buat_halaman_jurnal(self):
        """Halaman utama - task list"""
        self.item_jurnal = MDBottomNavigationItem(name='screen 2', text='Jurnal', icon='notebook-edit')
        jurnal_layout = MDBoxLayout(orientation='vertical', padding=15, spacing=10)

        # Input task
        input_area = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)
        self.task_input = MDTextField(hint_text='Ketik aktivitas...', mode="rectangle")
        btn_add = MDRaisedButton(text='ADD', on_release=lambda x: self.tambah_tugas())
        input_area.add_widget(self.task_input)
        input_area.add_widget(btn_add)
        jurnal_layout.add_widget(input_area)

        # List task
        self.scroll = ScrollView()
        self.list_tugas = MDGridLayout(cols=1, size_hint_y=None, spacing=10)
        self.list_tugas.bind(minimum_height=self.list_tugas.setter('height'))
        self.scroll.add_widget(self.list_tugas)
        jurnal_layout.add_widget(self.scroll)

        self.item_jurnal.add_widget(jurnal_layout)

        # Tab Logout
        self.item_logout = MDBottomNavigationItem(
            name='screen_logout', text='Logout', icon='logout',
            on_tab_press=lambda x: self.proses_logout()
        )

        self.nav.add_widget(self.item_jurnal)
        self.nav.add_widget(self.item_logout)
        self.load_tasks()

    def tambah_tugas(self, text_val=None):
        """Add task via backend API"""
        teks = text_val if text_val else self.task_input.text.strip()
        if teks:
            try:
                # POST ke backend
                resp = requests.post(
                    f"{BACKEND_URL}/tasks",
                    json={"text": teks},
                    params={"token": self.user_token},
                    timeout=5
                )
                
                if resp.status_code == 200:
                    task_data = resp.json()
                    self.render_task_row(teks, task_data['id'])
                    if not text_val:
                        self.task_input.text = ""
                        self.task_input.focus = True
                    Snackbar(text="Task added!").open()
                else:
                    Snackbar(text="Failed to add task").open()
            except Exception as e:
                print(f"Add task error: {e}")
                Snackbar(text="Error adding task").open()

    def render_task_row(self, teks, task_id=None):
        """Render task row"""
        row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=5)
        row.task_id = task_id
        row.add_widget(MDCheckbox(size_hint_x=None, width=40))
        row.add_widget(MDLabel(text=teks, halign='left', valign='middle'))
        btn_del = MDIconButton(icon='trash-can', on_release=lambda x: self.hapus_baris(row))
        row.add_widget(btn_del)
        self.list_tugas.add_widget(row)

    def hapus_baris(self, row):
        """Delete task via backend API"""
        if hasattr(row, 'task_id') and row.task_id:
            try:
                resp = requests.delete(
                    f"{BACKEND_URL}/tasks/{row.task_id}",
                    params={"token": self.user_token},
                    timeout=5
                )
                if resp.status_code == 200:
                    self.list_tugas.remove_widget(row)
                    Snackbar(text="Task deleted!").open()
                else:
                    Snackbar(text="Failed to delete").open()
            except Exception as e:
                print(f"Delete error: {e}")
        else:
            self.list_tugas.remove_widget(row)

    def load_tasks(self):
        """Load tasks dari backend"""
        try:
            resp = requests.get(
                f"{BACKEND_URL}/tasks",
                params={"token": self.user_token},
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                tasks = data.get('tasks', [])
                for task in tasks:
                    self.render_task_row(task['text'], task['id'])
                Snackbar(text=f"Loaded {len(tasks)} tasks").open()
            else:
                Snackbar(text="Failed to load tasks").open()
        except Exception as e:
            print(f"Load tasks error: {e}")
            # Fallback ke local file
            if os.path.exists(self.file_path):
                with open(self.file_path, "r") as f:
                    for line in f:
                        if line.strip():
                            self.render_task_row(line.strip())

    def proses_logout(self):
        """Logout"""
        try:
            self.nav.remove_widget(self.item_jurnal)
            self.nav.remove_widget(self.item_logout)
            self.nav.add_widget(self.item_login)
            self.nav.switch_tab('screen 1')
            Snackbar(text="Logged out").open()
        except Exception as e:
            print(f"Logout error: {e}")

if __name__ == "__main__":
    WellbeingApp().run()
