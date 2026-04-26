import os
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

# Firebase config
API_KEY = "AIzaSyCBNE1-04xpDNBGvo-wqypfcHln0vZDX0s"
BACKEND_URL = "http://localhost:8000"

class WellbeingApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        self.file_path = os.path.join(os.path.dirname(__file__), "tasks.txt")
        self.nav = MDBottomNavigation()
        self.user_token = None

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

    def login_firebase(self, email, password):
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
            payload = {"email": email, "password": password, "returnSecureToken": True}
            resp = requests.post(url, json=payload, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f"Firebase error: {e}")
            return None

    def proses_login(self, instance):
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        
        try:
            user = self.login_firebase(email, password)
            if not user:
                print("Firebase login gagal!")
                return
            
            self.user_token = user.get('idToken')
            
            resp = requests.post(
                f"{BACKEND_URL}/login",
                params={"token": self.user_token},
                timeout=5
            )
            
            if resp.status_code == 200:
                data = resp.json()
                self.user_id = data.get('user_id')
                print(f"Login Berhasil! User ID: {self.user_id}")
                self.buat_halaman_jurnal()
                Clock.schedule_once(self.pindah_halaman, 0.2)
            else:
                print(f"Backend error: {resp.status_code}")
        except Exception as e:
            print(f"Login error: {e}")

    def pindah_halaman(self, dt):
        self.nav.switch_tab('screen 2')
        Clock.schedule_once(lambda x: self.nav.remove_widget(self.item_login), 0.1)

    def buat_halaman_jurnal(self):
        self.item_jurnal = MDBottomNavigationItem(name='screen 2', text='Jurnal', icon='notebook-edit')
        jurnal_layout = MDBoxLayout(orientation='vertical', padding=15, spacing=10)

        input_area = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)
        self.task_input = MDTextField(hint_text='Ketik aktivitas...', mode="rectangle")
        btn_add = MDRaisedButton(text='ADD', on_release=lambda x: self.tambah_tugas())
        input_area.add_widget(self.task_input)
        input_area.add_widget(btn_add)
        jurnal_layout.add_widget(input_area)

        self.scroll = ScrollView()
        self.list_tugas = MDGridLayout(cols=1, size_hint_y=None, spacing=10)
        self.list_tugas.bind(minimum_height=self.list_tugas.setter('height'))
        self.scroll.add_widget(self.list_tugas)
        jurnal_layout.add_widget(self.scroll)

        self.item_jurnal.add_widget(jurnal_layout)

        self.item_logout = MDBottomNavigationItem(
            name='screen_logout', text='Logout', icon='logout',
            on_tab_press=lambda x: self.proses_logout()
        )

        self.nav.add_widget(self.item_jurnal)
        self.nav.add_widget(self.item_logout)
        self.load_tasks()

    def tambah_tugas(self):
        teks = self.task_input.text.strip()
        if teks:
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/tasks",
                    json={"text": teks},
                    params={"token": self.user_token},
                    timeout=5
                )
                
                if resp.status_code == 200:
                    task_data = resp.json()
                    self.render_task_row(teks, task_data['id'])
                    self.task_input.text = ""
                    print("Task added!")
            except Exception as e:
                print(f"Add task error: {e}")

    def render_task_row(self, teks, task_id=None):
        row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=5)
        row.task_id = task_id
        row.add_widget(MDCheckbox(size_hint_x=None, width=40))
        row.add_widget(MDLabel(text=teks, halign='left', valign='middle'))
        btn_del = MDIconButton(icon='trash-can', on_release=lambda x: self.hapus_baris(row))
        row.add_widget(btn_del)
        self.list_tugas.add_widget(row)

    def hapus_baris(self, row):
        if hasattr(row, 'task_id') and row.task_id:
            try:
                requests.delete(
                    f"{BACKEND_URL}/tasks/{row.task_id}",
                    params={"token": self.user_token},
                    timeout=5
                )
                self.list_tugas.remove_widget(row)
                print("Task deleted!")
            except Exception as e:
                print(f"Delete error: {e}")

    def load_tasks(self):
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
                print(f"Loaded {len(tasks)} tasks")
        except Exception as e:
            print(f"Load tasks error: {e}")

    def proses_logout(self):
        try:
            self.nav.remove_widget(self.item_jurnal)
            self.nav.remove_widget(self.item_logout)
            self.nav.add_widget(self.item_login)
            self.nav.switch_tab('screen 1')
        except Exception as e:
            print(f"Logout error: {e}")

if __name__ == "__main__":
    WellbeingApp().run()
