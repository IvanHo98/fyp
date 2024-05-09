from kivy.app import App
from kivy.lang import Builder
from kivy.properties import (StringProperty,NumericProperty,ObjectProperty,BooleanProperty)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.image import AsyncImage
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.graphics.texture import Texture
from kivy.core.window import Window
import cv2
from kivy.metrics import dp
from kivy.uix.camera import Camera
from kivy.core.audio import SoundLoader
from pymongo import MongoClient
import random
import json
import numpy
import pandas as pd
import os

Builder.load_file("./main.kv")
Window.clearcolor = (1, 1, 1, 1)

class UserInfo(Screen):
    def __init__(self, **kwargs):
        super(UserInfo, self).__init__(**kwargs)
        self.name = ""
        self.age = ""
        self.gender = ""

    def show_pop(self, message):
        popup = Popup(title="x_x", content=Label(text=message))
        popup.open()

    def reset(self):
        self.ids.name.text = ""
        self.ids.age.text = ""
        self.ids.male.state = "normal"
        self.ids.female.state = "normal"

    def next(self):
        name = self.ids.name.text
        age = self.ids.age.text
        gender = "Male" if self.ids.male.state == "down" else "Female"
        if name.isdigit() or not name.strip():
            self.show_pop("請輸入有效的姓名")
        elif not age.strip() or not age.isdigit() or int(age) < 12 or int(age) > 100:
            self.show_pop("請輸入12至100的年齡")
        elif self.ids.male.state == "normal" and self.ids.female.state == "normal":
            self.show_pop("請選擇性別")
        else:
            user_data = {
                "name": name,
                "age": int(age),
                "gender": gender
            }
            with open("./user_info.json", "w") as json_file:
                json.dump(user_data, json_file)
            
            app = App.get_running_app()
            self.name = name
            self.age = age
            self.gender = gender
            app.root.current = "main"


class MainScreen(Screen):
    def ready_screen(self):
        app = App.get_running_app()
        app.sm.current = "ready"
    def display_screen(self):
        app = App.get_running_app()
        app.sm.current = "display"

class PreferencesScreen(Screen):
    preferences = StringProperty()

class ReadyScreen(Screen):
    timer = NumericProperty(15)
    timer_event = None

    def on_enter(self):
        self.reset_timer()
        self.start_timer()

    def start_timer(self):
        if not self.timer_event:
            self.timer_event = Clock.schedule_interval(self.update_timer, 1)

    def reset_timer(self):
        self.timer = 15

    def update_timer(self, dt):
        self.timer -= 1
        if self.timer <= 0:
            self.stop_timer()
            self.quiz()

    def stop_timer(self):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

    def quiz(self):
        self.stop_timer()
        app = App.get_running_app()
        app.root.current = "quiz"

    def main(self):
        self.stop_timer()
        app = App.get_running_app()
        app.root.current = "main"


class QuizScreen(Screen):
    user_selections = []
    user_info = {}
    
    def __init__(self, **kwargs):
        super(QuizScreen, self).__init__(**kwargs)
        self.questions = []
        self.question_layout = BoxLayout(
            orientation="vertical", pos_hint={"center_y": 0.7}, size_hint=(1, 0.3)
        )
        self.add_widget(self.question_layout)
        self.answer_buttons = []
        self.current_question_index = 0
        self.score = 0
        self.score_label = Label(
            text="", pos_hint={"x": 0.5, "y": 0.4}, size_hint=(None, None)
        )
        self.add_widget(self.score_label)
        self.answer_layout = BoxLayout(orientation="vertical", size_hint=(1, 1.6))
        self.add_widget(self.answer_layout)
        self.load_questions_from_json("./question.json")
        self.timer = None
        self.timer_label = Label(
            text="",
            pos_hint={"x": 0.8, "y": 0.8},
            color=get_color_from_hex("#FF0000"),
            size_hint=(None, None),
            font_size="70sp",
        )
        self.add_widget(self.timer_label)

    def load_questions_from_json(self, filename):
            with open(filename, "r", encoding="utf-8") as file:
                self.questions = json.load(file)


    def display_question(self, question_index):
        if len(self.questions) == 0:
            return

        question = self.questions[question_index]

        self.question_layout.clear_widgets()
        self.question_layout.add_widget(
            Label(text=f"Question {question_index + 1}: \n{question['question']}")
        )

        self.answer_layout.clear_widgets()
        if "image_file" in question:
            image_path = question["image_file"]
            image = Image(
                source=image_path,
                size_hint=(1, 0.9),
            )
            self.question_layout.add_widget(image)

        if question["type"] == "multiple_choice":
            self.create_multiple_choice_buttons(question["answers"])
        elif question["type"] == "true_false":
            self.create_true_false_buttons()

    def on_enter(self):
        self.score = 0
        self.display_question(0)
        self.current_question_index = 0
        self.start_timer()

    def create_multiple_choice_buttons(self, answers):
        button_layout = BoxLayout(
            orientation="horizontal", spacing=10, size_hint=(1, 0.2)
        )
        for answer in answers:
            button = Button(text=answer, size_hint=(1, 0.2), size=(300, 300))
            button.bind(on_release=self.check_answer)
            self.answer_buttons.append(button)
            button_layout.add_widget(button)
        self.answer_layout.add_widget(button_layout)

    def create_true_false_buttons(self):
        button_layout = BoxLayout(orientation="horizontal", spacing=50)

        true_button = Button(text="是", size_hint=(1, 0.2), size=(150, 50))
        true_button.bind(on_release=self.check_answer)
        self.answer_buttons.append(true_button)
        button_layout.add_widget(true_button)

        false_button = Button(text="否", size_hint=(1, 0.2), size=(150, 50))
        false_button.bind(on_release=self.check_answer)
        self.answer_buttons.append(false_button)
        button_layout.add_widget(false_button)

        self.answer_layout.clear_widgets()
        self.answer_layout.add_widget(button_layout)

    def check_answer(self, button):
        question = self.questions[self.current_question_index]
        selected_answer = button.text
        self.user_selections.append(selected_answer)
        
        if button.text == question["correct_answer"]:
            self.score += 1
        self.current_question_index += 1
        if self.current_question_index < len(self.questions):
            self.stop_timer()
            self.display_question(self.current_question_index)
            self.start_timer()
        else:
            app = App.get_running_app()
            app.root.current = "result"

    def on_leave(self):
        self.timer_label.text = ""
        self.stop_timer()
        
        quiz_selections = {
            "score": self.score,
            "selections": []
        }

        for i, question in enumerate(self.questions):
            quiz_selections["selections"].append({
                "question": question["question"],
                "selected_answer": self.user_selections[i],
                "is_correct": self.answer_buttons[i].text == question["correct_answer"]
            })

        with open("./user_info.json", "r") as json_file:
            user_data = json.load(json_file)
            user_data["quiz_selections"] = quiz_selections

        with open("./user_info.json", "w") as json_file:
            json.dump(user_data, json_file)

    def start_timer(self):
        self.stop_timer() 
        self.timer_label.text = "5"
        self.timer = Clock.schedule_interval(self.update_timer, 1)

    def stop_timer(self):
        if self.timer:
            self.timer.cancel()

    def update_timer(self, dt):
        remaining_time = int(self.timer_label.text) - 1
        self.timer_label.text = str(remaining_time)

        if remaining_time <= 0:
            self.stop_timer()
            self.current_question_index += 1

            if self.current_question_index < len(self.questions):
                self.display_question(self.current_question_index)
                self.start_timer()
            else:
                app = App.get_running_app()
                app.root.current = "result"
        else:
            if (
                remaining_time == 5
                and self.current_question_index < len(self.questions) - 1
            ):
                self.stop_timer()
                self.current_question_index += 1
                self.display_question(self.current_question_index)
                self.start_timer()
                self.timer_label.text = "5"

class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super(ResultScreen, self).__init__(**kwargs)
        self.result_label = Label(
            text="", pos_hint={"center_x": 0.45, "center_y": 0.75}, size_hint=(None, None),color=(0, 0, 0, 1), font_size=36
        )
        self.add_widget(self.result_label)
        
        self.suggestion_label = Label(
            text="", pos_hint={"center_x": 0.5, "center_y": 0.5}, size_hint=(None, None),color=(0, 0, 0, 1), font_size=36
        )
        self.add_widget(self.suggestion_label)

    def on_enter(self):
        app = App.get_running_app()
        quiz_screen = app.root.get_screen("quiz")
        score = quiz_screen.score
        total_questions = len(quiz_screen.questions)
        self.result_label.text = (
            f"測試完成!\n你的分數: {score}/{total_questions}\n "
        )
        
        if score >= 17:
            self.result_label.text += "恭喜你！你經過初步判斷並沒有失智症\n"
            self.suggestion_label.text = (
                #Label(text="恭喜你！你經過初步判斷並沒有失智症", background_color=get_color_from_hex("#00FF00")) +
                "請在eCare網站中取得報告/建議"
            )
        elif score <= 16 and score >= 13:
            self.result_label.text += "程度:初步判斷為輕微失智\n"
            self.suggestion_label.text = (
                "請在eCare網站中取得報告/建議"
            )
        elif score <= 12 and score >= 9:
            self.result_label.text += "程度:初步判斷為中等失智\n"
            self.suggestion_label.text = (
                "請在eCare網站中取得報告/建議"
            )
        else:
            self.result_label.text += "程度:初步判斷為嚴重失智\n"
            self.suggestion_label.text = (
                "請在eCare網站中取得報告/建議"
            )
        
    def main(self, *args):
        app = App.get_running_app()
        app.root.current = "main"

class MusicSelect(Screen):
    def play_audio(self, button):
        if button.state == 'down':
            sound = SoundLoader.load(button.sound_file)
            if sound:
                sound.play()
                self.update_user_info(button.text)
        else:
            sound.stop()
            
    def update_user_info(self, music_preference):
        with open('./user_info.json', 'r') as file:
            user_info = json.load(file)

        user_info['music_preference'] = music_preference

        with open('./user_info.json', 'w') as file:
            json.dump(user_info, file)
    def show_popup(self):
        content = Label(text="已提交选择，请返回主选单")
        popup = Popup(title="提示", content=content, size_hint=(None, None), size=(400, 200))
        popup.open()
    
class FacePhoto(Screen):
    def build(self):
        camera = Camera()
        camera.resolution = (800, 800)

        def take_photo(instance):
            # Capture the current frame from the camera
            texture = camera.texture
            image = Image(texture=texture)

            # Create a filename for the photo
            filename = "face_photo.png"

            # Save the image as a PNG file
            image.texture.save(filename, flipped=False)

            # Print the path to the saved photo
            print("Photo saved:", os.path.abspath(filename))

        # Create a button to take the photo
        button = Button(text="Take Photo", size_hint=(None, None), size=(150, 50), pos_hint={"center_x": 0.5}, on_release=take_photo)

        # Create a layout and add the camera and button to it
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(camera)
        layout.add_widget(button)

        return layout

class AppManager(App):
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(UserInfo(name="userinfo"))
        self.sm.add_widget(MainScreen(name="main"))
        self.sm.add_widget(PreferencesScreen(name="preferences"))
        self.sm.add_widget(ReadyScreen(name="ready"))
        self.sm.add_widget(QuizScreen(name="quiz"))
        self.sm.add_widget(ResultScreen(name="result"))
        self.sm.add_widget(FacePhoto(name="cam"))
        self.sm.add_widget(MusicSelect(name="music"))
        return self.sm

if __name__ == "__main__":
    AppManager().run()