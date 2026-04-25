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
from kivymd.uix.snackbar import Snackbar

# --- KONFIGURASI ---
BACKEND_URL = "http://localhost:8000"

class WellbeingApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        self.file_path = os.path.join(os.path.dirname(__file__), "tasks.txt")
        self.nav = MDBottomNavigation()

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

    def login_backend(self, email, password):
        try:
            url = f"{BACKEND_URL}/login"
            resp = requests.post(url, params={"email": email, "password": password}, timeout=5)
            return resp.json() if resp.status_code == 200 else None
        except Exception as e:
            print(f"Login error: {e}")
            return None

    def save_tasks_backend(self, tasks):
        if hasattr(self, 'user_id'):
            try:
                print(f"Tasks saved for user {self.user_id}")
            except Exception as e:
                print(f"Save error: {e}")

    def load_tasks_backend(self):
        if hasattr(self, 'user_id'):
            try:
                url = f"{BACKEND_URL}/tasks/{self.user_id}"
                resp = requests.get(url, timeout=5)
                data = resp.json()
                return data.get("tasks", []) if resp.status_code == 200 else None
            except Exception as e:
                print(f"Load error: {e}")
                return None
        return None

    def proses_login(self, instance):
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        user = self.login_backend(email, password)
        if user:
            self.user_token = user.get('token')
            self.user_id = user.get('user_id')
            print(f"Login Berhasil! ID User: {self.user_id}")
            self.buat_halaman_jurnal()
            Clock.schedule_once(self.pindah_halaman, 0.2)
        else:
            Snackbar(text="Login gagal!", duration=2).open()

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

    def tambah_tugas(self, text_val=None):
        teks = text_val if text_val else self.task_input.text
        if teks.strip():
            self.render_task_row(teks)
            if not text_val:
                self.save_tasks()
                self.task_input.text = ""
                self.task_input.focus = True

    def render_task_row(self, teks):
        row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=5)
        row.add_widget(MDCheckbox(size_hint_x=None, width=40))
        row.add_widget(MDLabel(text=teks, halign='left', valign='middle'))
        btn_del = MDIconButton(icon='trash-can', on_release=lambda x: self.hapus_baris(row))
        row.add_widget(btn_del)
        self.list_tugas.add_widget(row)

    def hapus_baris(self, row):
        self.list_tugas.remove_widget(row)
        Clock.schedule_once(self.save_tasks, 0.2)

    def save_tasks(self, *args):
        semua_tugas = []
        for child in reversed(self.list_tugas.children):
            try:
                if len(child.children) >= 2:
                    teks = child.children[1].text
                    semua_tugas.append(teks)
            except:
                continue

        with open(self.file_path, "w") as f:
            for t in semua_tugas:
                f.write(t + "\n")

        self.save_tasks_backend(semua_tugas)

    def load_tasks(self):
        self.list_tugas.clear_widgets()
        data_backend = self.load_tasks_backend()
        if data_backend:
            for t in data_backend:
                self.render_task_row(t)
        elif os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                for line in f:
                    if line.strip():
                        self.render_task_row(line.strip())

    def proses_logout(self):
        self.nav.remove_widget(self.item_jurnal)
        self.nav.remove_widget(self.item_logout)
        self.nav.add_widget(self.item_login)
        self.nav.switch_tab('screen 1')

if __name__ == "__main__":
    WellbeingApp().run()
