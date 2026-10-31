import json
import yaml
from datetime import datetime
from pathlib import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock

import os

def get_data_dir():
    # На Android Kivy хранит данные в специальной папке
    if hasattr(os, 'environ') and 'ANDROID_PRIVATE' in os.environ:
        base = Path(os.environ['ANDROID_PRIVATE'])
    else:
        # На ПК — рядом с main.py
        base = Path(__file__).parent.resolve()
    base.mkdir(parents=True, exist_ok=True)
    return base

DATA_DIR = get_data_dir()
FILES = {
    "catalog": DATA_DIR / "pcheloeat.yaml",
    "diary": DATA_DIR / "diary.yaml",
    "weight": DATA_DIR / "weight.yaml",
    "user": DATA_DIR / "user.json"
}

def load_yaml(path):
    if not path.exists(): return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

def calc_tdee(gender, age, height, weight, activity, goal):
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    factors = {
        "Сидячий (нет тренировок)": 1.2,
        "Лёгкая активность (1-3 тр/нед)": 1.375,
        "Средняя активность (3-5 тр/нед)": 1.55,
        "Высокая активность (6-7 тр/нед)": 1.725
    }
    tdee = bmr * factors.get(activity, 1.2)
    if goal == "gain": target = tdee * 1.15
    elif goal == "lose": target = tdee * 0.85
    else: target = tdee
    proteins = (target * 0.3) / 4
    fats = (target * 0.2) / 9
    carbs = (target * 0.5) / 4
    return tdee, target, proteins, fats, carbs

def get_daily_stats():
    diary = load_yaml(FILES["diary"])
    today = datetime.now().strftime("%Y-%m-%d")
    total_kcal = total_b = total_zh = total_u = 0
    if today in diary:
        for meals in diary[today].values():
            for item in meals:
                mass = item.get("mass", 100)
                total_kcal += item.get("kcal", 0) * (mass / 100.0)
                total_b += item.get("b", 0)
                total_zh += item.get("zh", 0)
                total_u += item.get("u", 0)
    user = {}
    if FILES["user"].exists():
        with open(FILES["user"], "r", encoding="utf-8") as f:
            user = json.load(f)
    _, target, _, _, _ = calc_tdee(
        user.get("gender", "female"), user.get("age", 30),
        user.get("height", 170), user.get("weight", 70),
        user.get("activity", "Сидячий (нет тренировок)"),
        user.get("goal", "maintain")
    )
    percent = (total_kcal / max(target, 1)) * 100
    return total_kcal, target, percent, total_b, total_zh, total_u

# --- KIVY UI ---
class DiaryTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=10, spacing=10, **kwargs)
        self.add_widget(Label(text="Дневник питания", size_hint_y=None, height=dp(30), font_size=dp(18)))
        
        # Список записей (простой скролл)
        scroll = ScrollView(size_hint=(1, 1))
        self.grid = GridLayout(cols=1, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        self.add_widget(scroll)
        
        # Форма добавления
        form = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(60), spacing=10)
        self.ti_product = TextInput(hint_text="Продукт", size_hint_x=0.5)
        self.ti_mass = TextInput(hint_text="Масса, г", size_hint_x=0.3, input_filter="float")
        btn_add = Button(text="Добавить", size_hint_x=0.2, background_color=(0.6, 0.4, 0.8, 1))
        btn_add.bind(on_press=self.add_entry)
        form.add_widget(self.ti_product)
        form.add_widget(self.ti_mass)
        form.add_widget(btn_add)
        self.add_widget(form)
        
        self.refresh_list()

    def add_entry(self, instance):
        product = self.ti_product.text.strip()
        try:
            mass = float(self.ti_mass.text.strip())
        except:
            return
        if not product: return
        
        today = datetime.now().strftime("%Y-%m-%d")
        diary = load_yaml(FILES["diary"])
        if today not in diary: diary[today] = {}
        meal = "Обед"  # для простоты
        if meal not in diary[today]: diary[today][meal] = []
        
        # Здесь можно подтянуть КБЖУ из каталога, пока ставим заглушку
        diary[today][meal].append({
            "name": product,
            "mass": mass,
            "kcal": 200,  # заглушка
            "b": 20,
            "zh": 5,
            "u": 30
        })
        save_yaml(FILES["diary"], diary)
        self.ti_product.text = ""
        self.ti_mass.text = ""
        self.refresh_list()

    def refresh_list(self):
        self.grid.clear_widgets()
        diary = load_yaml(FILES["diary"])
        today = datetime.now().strftime("%Y-%m-%d")
        if today in diary:
            for meal, items in diary[today].items():
                self.grid.add_widget(Label(text=f"--- {meal} ---", size_hint_y=None, height=dp(25)))
                for i in items:
                    txt = f"{i['name']} — {i['mass']} г, {i['kcal']} ккал"
                    self.grid.add_widget(Label(text=txt, size_hint_y=None, height=dp(25), color=(0,0,0,1)))
        else:
            self.grid.add_widget(Label(text="Нет записей на сегодня", size_hint_y=None, height=dp(25)))

class WeightTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=10, spacing=10, **kwargs)
        self.add_widget(Label(text="Контроль веса", size_hint_y=None, height=dp(30), font_size=dp(18)))
        
        self.ti_weight = TextInput(hint_text="Вес (кг)", size_hint_y=None, height=dp(40), input_filter="float")
        btn = Button(text="Записать вес", size_hint_y=None, height=dp(40), background_color=(0.4, 0.6, 0.8, 1))
        btn.bind(on_press=self.save_weight)
        
        self.list_scroll = ScrollView(size_hint=(1, 1))
        self.list_grid = GridLayout(cols=1, size_hint_y=None)
        self.list_grid.bind(minimum_height=self.list_grid.setter('height'))
        self.list_scroll.add_widget(self.list_grid)
        
        self.add_widget(self.ti_weight)
        self.add_widget(btn)
        self.add_widget(self.list_scroll)
        self.refresh_list()

    def save_weight(self, instance):
        try:
            weight = float(self.ti_weight.text)
            logs = load_yaml(FILES["weight"])
            logs.append({"date": datetime.now().strftime("%Y-%m-%d"), "weight_kg": weight})
            save_yaml(FILES["weight"], logs)
            self.ti_weight.text = ""
            self.refresh_list()
        except: pass

    def refresh_list(self):
        self.list_grid.clear_widgets()
        logs = load_yaml(FILES["weight"])
        for l in sorted(logs, key=lambda x: x.get("date"), reverse=True):
            txt = f"{l['date']} — {l['weight_kg']} кг"
            self.list_grid.add_widget(Label(text=txt, size_hint_y=None, height=dp(25), color=(0,0,0,1)))

class StatsTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=10, spacing=10, **kwargs)
        self.add_widget(Label(text="Статистика", size_hint_y=None, height=dp(30), font_size=dp(18)))
        self.lbl_stats = Label(text="Загрузка...", size_hint_y=1)
        self.add_widget(self.lbl_stats)
        Clock.schedule_once(self.update_stats, 0.1)

    def update_stats(self, dt):
        kcal, target, percent, b, zh, u = get_daily_stats()
        color = "green" if percent <= 100 else "red"
        text = (
            f"Сегодня: {kcal:.0f} / {target:.0f} ккал ({percent:.0f}%)\n\n"
            f"Белки: {b:.0f} г | Жиры: {zh:.0f} г | Углеводы: {u:.0f} г"
        )
        self.lbl_stats.text = text
        self.lbl_stats.color = (0, 1, 0, 1) if percent <= 100 else (1, 0, 0, 1)

class ProfileTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=10, spacing=10, **kwargs)
        self.add_widget(Label(text="Профиль", size_hint_y=None, height=dp(30), font_size=dp(18)))
        # Тут можно добавить поля для редактирования профиля, пока заглушка
        self.add_widget(Label(text="Здесь будут параметры профиля (рост, вес, цель и т.д.)", size_hint_y=1))

class HudeemApp(App):
    def build(self):
        Window.size = (400, 700)  # эмуляция мобильного экрана на ПК
        panel = TabbedPanel(do_default_tab=False)
        
        diary_tab = TabbedPanelItem(text="Дневник")
        diary_tab.content = DiaryTab()
        panel.add_widget(diary_tab)
        
        weight_tab = TabbedPanelItem(text="Вес")
        weight_tab.content = WeightTab()
        panel.add_widget(weight_tab)
        
        stats_tab = TabbedPanelItem(text="Графики")
        stats_tab.content = StatsTab()
        panel.add_widget(stats_tab)
        
        profile_tab = TabbedPanelItem(text="Профиль")
        profile_tab.content = ProfileTab()
        panel.add_widget(profile_tab)
        
        return panel

if __name__ == "__main__":
    HudeemApp().run()
