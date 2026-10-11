# -*- coding: utf-8 -*-
# تطبيق إدارة الملفات - تطوير Nasser Al-Souri
import os
import time

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.core.window import Window
from kivy.clock import Clock

import crypto_utils
import file_ops
import storage_utils

DEVELOPER_NAME = "𝑵𝒂𝒔𝒔𝒆𝒓 𝑨𝒍-𝑺𝒐𝒖𝒓𝒊"
APP_TITLE = "مدير الملفات"

KV = """
#:import utils kivy.utils

<RootLabel@Label>:
    font_name: "fonts/Cairo-Regular.ttf" if app.has_arabic_font else ""
    color: 0.92, 0.92, 0.95, 1

<RootButton@Button>:
    font_name: "fonts/Cairo-Regular.ttf" if app.has_arabic_font else ""
    background_normal: ""
    background_color: 0.18, 0.45, 0.85, 1
    color: 1, 1, 1, 1

<FileRow@BoxLayout>:
    name: ""
    subtitle: ""
    is_dir: False
    size: dp(56)
    size_hint_y: None
    padding: dp(10), dp(4)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: (0.13, 0.13, 0.17, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    RootLabel:
        text: ("📁 " if root.is_dir else "📄 ") + root.name
        halign: "right"
        valign: "middle"
        text_size: self.size
        shorten: True
    RootLabel:
        text: root.subtitle
        size_hint_x: 0.3
        halign: "left"
        valign: "middle"
        text_size: self.size
        font_size: "12sp"
        color: 0.7, 0.7, 0.75, 1

<LockScreen>:
    name: "lock"
    BoxLayout:
        orientation: "vertical"
        padding: dp(30)
        spacing: dp(16)
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Widget:
            size_hint_y: 0.2
        RootLabel:
            text: "مدير الملفات"
            font_size: "26sp"
            size_hint_y: None
            height: dp(40)
            halign: "center"
            text_size: self.size
        RootLabel:
            text: "أدخل كلمة السر للدخول"
            font_size: "14sp"
            size_hint_y: None
            height: dp(30)
            halign: "center"
            text_size: self.size
        TextInput:
            id: pw_input
            hint_text: "كلمة السر"
            password: True
            multiline: False
            size_hint_y: None
            height: dp(48)
            font_size: "16sp"
            on_text_validate: root.try_unlock()
        RootButton:
            text: "دخول"
            size_hint_y: None
            height: dp(48)
            on_release: root.try_unlock()
        RootLabel:
            id: lock_error
            text: ""
            color: 0.9, 0.3, 0.3, 1
            size_hint_y: None
            height: dp(24)
            halign: "center"
            text_size: self.size
        Widget:

<BrowserScreen>:
    name: "browser"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: dp(6)
            spacing: dp(6)
            RootButton:
                text: "⬅ رجوع"
                size_hint_x: 0.2
                on_release: root.go_up()
            RootLabel:
                id: path_label
                text: root.current_path
                shorten: True
                halign: "right"
                valign: "middle"
                text_size: self.size
            RootButton:
                text: "⋮"
                size_hint_x: 0.15
                on_release: root.open_menu()
        BoxLayout:
            size_hint_y: None
            height: dp(44)
            padding: dp(6), 0
            spacing: dp(6)
            TextInput:
                id: search_box
                hint_text: "بحث عن ملف..."
                multiline: False
                on_text_validate: root.do_search(self.text)
            RootButton:
                text: "بحث"
                size_hint_x: 0.25
                on_release: root.do_search(search_box.text)
        ScrollView:
            GridLayout:
                id: file_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height
        BoxLayout:
            size_hint_y: None
            height: dp(52)
            padding: dp(4)
            spacing: dp(4)
            RootButton:
                text: "مفضلة"
                on_release: root.go_favorites()
            RootButton:
                text: "سلة المحذوفات"
                on_release: root.go_trash()
            RootButton:
                text: "التكرارات"
                on_release: root.go_duplicates()
            RootButton:
                text: "الإعدادات"
                on_release: root.go_settings()
            RootButton:
                text: "عن المطور"
                on_release: root.go_about()

<TrashScreen>:
    name: "trash"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: dp(6)
            RootButton:
                text: "⬅ رجوع"
                size_hint_x: 0.25
                on_release: root.go_back()
            RootLabel:
                text: "سلة المحذوفات"
                halign: "center"
                text_size: self.size
            RootButton:
                text: "تفريغ"
                size_hint_x: 0.3
                on_release: root.empty_all()
        ScrollView:
            GridLayout:
                id: trash_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height

<FavoritesScreen>:
    name: "favorites"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: dp(6)
            RootButton:
                text: "⬅ رجوع"
                size_hint_x: 0.3
                on_release: root.go_back()
            RootLabel:
                text: "المفضلة"
                halign: "center"
                text_size: self.size
        ScrollView:
            GridLayout:
                id: fav_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height

<DuplicatesScreen>:
    name: "duplicates"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: dp(6)
            RootButton:
                text: "⬅ رجوع"
                size_hint_x: 0.3
                on_release: root.go_back()
            RootLabel:
                text: "ملفات مكررة"
                halign: "center"
                text_size: self.size
            RootButton:
                text: "فحص"
                size_hint_x: 0.3
                on_release: root.scan()
        ScrollView:
            GridLayout:
                id: dup_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height

<SettingsScreen>:
    name: "settings"
    BoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(14)
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            RootButton:
                text: "⬅ رجوع"
                size_hint_x: 0.3
                on_release: root.go_back()
            RootLabel:
                text: "الإعدادات"
                halign: "center"
                text_size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            RootLabel:
                text: "إظهار الملفات المخفية"
                halign: "right"
                text_size: self.size
            Switch:
                id: hidden_switch
                on_active: root.toggle_hidden(self.active)
        RootButton:
            text: "تغيير كلمة السر الرئيسية"
            size_hint_y: None
            height: dp(48)
            on_release: root.change_password_popup()
        RootLabel:
            id: storage_info
            text: ""
            size_hint_y: None
            height: dp(80)
            halign: "right"
            text_size: self.size
        Widget:

<AboutScreen>:
    name: "about"
    BoxLayout:
        orientation: "vertical"
        padding: dp(24)
        spacing: dp(12)
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        RootButton:
            text: "⬅ رجوع"
            size_hint: None, None
            size: dp(100), dp(44)
            on_release: root.go_back()
        Widget:
            size_hint_y: 0.1
        RootLabel:
            text: "مدير الملفات"
            font_size: "24sp"
            size_hint_y: None
            height: dp(40)
            halign: "center"
            text_size: self.size
        RootLabel:
            text: "تطوير وبرمجة\\n""" + DEVELOPER_NAME + """\\n\\nجميع الحقوق محفوظة"
            font_size: "16sp"
            halign: "center"
            text_size: self.size
        Widget:

<TextEditorScreen>:
    name: "editor"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.08, 0.08, 0.1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: dp(6)
            RootButton:
                text: "إلغاء"
                size_hint_x: 0.25
                on_release: root.cancel()
            RootLabel:
                text: root.file_name
                halign: "center"
                text_size: self.size
            RootButton:
                text: "حفظ"
                size_hint_x: 0.25
                on_release: root.save()
        TextInput:
            id: editor_input
            font_size: "15sp"
"""


class LockScreen(Screen):
    def try_unlock(self):
        pw = self.ids.pw_input.text
        if crypto_utils.verify_master_password(pw):
            self.ids.lock_error.text = ""
            self.ids.pw_input.text = ""
            self.manager.current = "browser"
        else:
            self.ids.lock_error.text = "كلمة السر غير صحيحة"


class BrowserScreen(Screen):
    current_path = StringProperty("")
    clipboard_path = StringProperty("")
    clipboard_mode = StringProperty("")  # copy / cut
    selected_path = StringProperty("")

    def on_pre_enter(self):
        if not self.current_path:
            self.current_path = storage_utils.get_storage_root()
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        cfg = app.config_data
        entries = file_ops.list_dir(self.current_path, show_hidden=cfg.get("show_hidden", False))
        box = self.ids.file_list
        box.clear_widgets()
        for e in entries:
            row = self._build_row(e)
            box.add_widget(row)

    def _build_row(self, entry):
        from kivy.metrics import dp
        row = BoxLayout(size_hint_y=None, height=dp(56), padding=(10, 4), spacing=10)
        label_text = ("📁 " if entry["is_dir"] else "📄 ") + entry["name"]
        lbl = Label(text=label_text, halign="right", valign="middle", shorten=True)
        lbl.bind(size=lambda s, v: setattr(s, "text_size", v))
        sub = entry["name"] if entry["is_dir"] else file_ops.human_size(entry["size"])
        sub_lbl = Label(text=sub, size_hint_x=0.35, font_size="12sp", color=(0.7, 0.7, 0.75, 1))
        row.add_widget(lbl)
        row.add_widget(sub_lbl)

        from kivy.uix.behaviors import ButtonBehavior

        def on_touch(instance, touch):
            if row.collide_point(*touch.pos) and touch.is_double_tap is False:
                pass
            return False

        row.bind(on_touch_down=lambda inst, t: self._row_touched(entry, t, row))
        return row

    def _row_touched(self, entry, touch, row):
        if not row.collide_point(*touch.pos):
            return False
        if touch.is_double_tap:
            self.open_entry(entry)
        else:
            self.show_item_menu(entry)
        return True

    def open_entry(self, entry):
        if entry["is_dir"]:
            self.current_path = entry["path"]
            self.refresh()
        else:
            self.open_file_action(entry["path"])

    def go_up(self):
        parent = os.path.dirname(self.current_path.rstrip("/"))
        if parent and os.path.isdir(parent) and parent != self.current_path:
            self.current_path = parent
            self.refresh()

    def do_search(self, query):
        if not query:
            return
        app = App.get_running_app()
        cfg = app.config_data
        results = file_ops.search_files(self.current_path, query, show_hidden=cfg.get("show_hidden", False))
        self._show_results_popup(results, f"نتائج البحث: {query}")

    def _show_results_popup(self, results, title):
        from kivy.metrics import dp
        content = BoxLayout(orientation="vertical", spacing=4, padding=8)
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.gridlayout import GridLayout
        scroll = ScrollView()
        grid = GridLayout(cols=1, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        if not results:
            grid.add_widget(Label(text="لا توجد نتائج", size_hint_y=None, height=dp(40)))
        for r in results:
            btn = Button(text=f"{r['name']}  ({file_ops.human_size(r['size'])})",
                         size_hint_y=None, height=dp(44))
            btn.bind(on_release=lambda b, p=r["path"]: self._goto_result(p))
            grid.add_widget(btn)
        scroll.add_widget(grid)
        content.add_widget(scroll)
        close_btn = Button(text="إغلاق", size_hint_y=None, height=dp(44))
        popup = Popup(title=title, content=content, size_hint=(0.9, 0.85))
        close_btn.bind(on_release=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    def _goto_result(self, path):
        self.current_path = os.path.dirname(path)
        self.refresh()

    def show_item_menu(self, entry):
        from kivy.metrics import dp
        path = entry["path"]
        content = BoxLayout(orientation="vertical", spacing=6, padding=8)
        actions = [
            ("فتح", lambda: self.open_entry(entry)),
            ("إعادة تسمية", lambda: self.rename_popup(path)),
            ("نسخ", lambda: self.copy_to_clipboard(path, "copy")),
            ("قص", lambda: self.copy_to_clipboard(path, "cut")),
            ("حذف إلى السلة", lambda: self.delete_to_trash(path)),
            ("حذف نهائي", lambda: self.delete_permanent_confirm(path)),
            ("تشفير", lambda: self.encrypt_popup(path)),
            ("فك تشفير", lambda: self.decrypt_popup(path)),
            ("إضافة للمفضلة", lambda: self.add_favorite(path)),
            ("معلومات", lambda: self.show_info(entry)),
            ("ضغط (ZIP)", lambda: self.zip_item(path)),
        ]
        if entry["name"].lower().endswith(".zip"):
            actions.append(("فك الضغط", lambda: self.unzip_item(path)))
        if not entry["is_dir"] and self._is_text_file(entry["name"]):
            actions.append(("تحرير النص", lambda: self.edit_text(path)))

        popup = Popup(title=entry["name"], size_hint=(0.85, 0.8))
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.gridlayout import GridLayout
        scroll = ScrollView()
        grid = GridLayout(cols=1, size_hint_y=None, spacing=4)
        grid.bind(minimum_height=grid.setter("height"))
        for label, fn in actions:
            btn = Button(text=label, size_hint_y=None, height=dp(46))

            def make_cb(f=fn):
                def cb(instance):
                    popup.dismiss()
                    f()
                return cb
            btn.bind(on_release=make_cb())
            grid.add_widget(btn)
        scroll.add_widget(grid)
        content.add_widget(scroll)
        popup.content = content
        popup.open()

    @staticmethod
    def _is_text_file(name):
        return os.path.splitext(name)[1].lower() in {".txt", ".md", ".json", ".py", ".log", ".csv"}

    def open_file_action(self, path):
        if self._is_text_file(os.path.basename(path)):
            self.edit_text(path)
        else:
            self._toast(f"تم اختيار: {os.path.basename(path)}")

    def rename_popup(self, path):
        content = BoxLayout(orientation="vertical", spacing=8, padding=10)
        ti = TextInput(text=os.path.basename(path), multiline=False)
        content.add_widget(ti)
        btn_row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        popup = Popup(title="إعادة تسمية", content=content, size_hint=(0.85, 0.35))

        def confirm(_):
            try:
                file_ops.rename_item(path, ti.text)
                self.refresh()
            except OSError as e:
                self._toast(str(e))
            popup.dismiss()

        ok_btn = Button(text="تأكيد")
        ok_btn.bind(on_release=confirm)
        cancel_btn = Button(text="إلغاء", on_release=popup.dismiss)
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        popup.open()

    def copy_to_clipboard(self, path, mode):
        self.clipboard_path = path
        self.clipboard_mode = mode
        self._toast("تم النسخ" if mode == "copy" else "تم القص")

    def paste_here(self):
        if not self.clipboard_path:
            return
        try:
            if self.clipboard_mode == "copy":
                file_ops.copy_item(self.clipboard_path, self.current_path)
            else:
                file_ops.move_item(self.clipboard_path, self.current_path)
                self.clipboard_path = ""
            self.refresh()
        except OSError as e:
            self._toast(str(e))

    def delete_to_trash(self, path):
        try:
            file_ops.move_to_trash(path, storage_utils.get_storage_root())
            self.refresh()
        except OSError as e:
            self._toast(str(e))

    def delete_permanent_confirm(self, path):
        content = BoxLayout(orientation="vertical", spacing=8, padding=10)
        content.add_widget(Label(text=f"حذف نهائي لـ {os.path.basename(path)}؟"))
        row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        popup = Popup(title="تأكيد الحذف", content=content, size_hint=(0.85, 0.35))

        def do_delete(_):
            try:
                file_ops.permanent_delete(path)
                self.refresh()
            except OSError as e:
                self._toast(str(e))
            popup.dismiss()

        row.add_widget(Button(text="حذف", on_release=do_delete))
        row.add_widget(Button(text="إلغاء", on_release=popup.dismiss))
        content.add_widget(row)
        popup.open()

    def encrypt_popup(self, path):
        self._password_popup("تشفير الملف", lambda pw: self._do_encrypt(path, pw))

    def decrypt_popup(self, path):
        self._password_popup("فك تشفير الملف", lambda pw: self._do_decrypt(path, pw))

    def _password_popup(self, title, on_confirm):
        content = BoxLayout(orientation="vertical", spacing=8, padding=10)
        ti = TextInput(hint_text="كلمة السر", password=True, multiline=False)
        content.add_widget(ti)
        row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        popup = Popup(title=title, content=content, size_hint=(0.85, 0.35))

        def confirm(_):
            pw = ti.text
            popup.dismiss()
            if pw:
                on_confirm(pw)

        row.add_widget(Button(text="تأكيد", on_release=confirm))
        row.add_widget(Button(text="إلغاء", on_release=popup.dismiss))
        content.add_widget(row)
        popup.open()

    def _do_encrypt(self, path, pw):
        try:
            crypto_utils.encrypt_file(path, pw)
            self.refresh()
            self._toast("تم التشفير")
        except Exception as e:
            self._toast(f"خطأ: {e}")

    def _do_decrypt(self, path, pw):
        try:
            crypto_utils.decrypt_file(path, pw)
            self.refresh()
            self._toast("تم فك التشفير")
        except Exception as e:
            self._toast(f"خطأ: {e}")

    def add_favorite(self, path):
        app = App.get_running_app()
        cfg = app.config_data
        favs = cfg.setdefault("favorites", [])
        if path not in favs:
            favs.append(path)
            crypto_utils.save_config(cfg)
        self._toast("أُضيف للمفضلة")

    def show_info(self, entry):
        stat = os.stat(entry["path"])
        info = (
            f"الاسم: {entry['name']}\n"
            f"الحجم: {file_ops.human_size(stat.st_size)}\n"
            f"آخر تعديل: {time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))}\n"
            f"المسار: {entry['path']}"
        )
        popup = Popup(title="معلومات الملف",
                       content=Label(text=info, halign="center"),
                       size_hint=(0.85, 0.4))
        popup.open()

    def zip_item(self, path):
        dst = path.rstrip("/") + ".zip"
        try:
            file_ops.zip_items([path], dst)
            self.refresh()
            self._toast("تم الضغط")
        except OSError as e:
            self._toast(str(e))

    def unzip_item(self, path):
        dst_dir = os.path.splitext(path)[0]
        os.makedirs(dst_dir, exist_ok=True)
        try:
            file_ops.unzip_file(path, dst_dir)
            self.refresh()
            self._toast("تم فك الضغط")
        except OSError as e:
            self._toast(str(e))

    def edit_text(self, path):
        app = App.get_running_app()
        editor = app.sm.get_screen("editor")
        editor.load_file(path)
        app.sm.current = "editor"

    def new_folder_popup(self):
        content = BoxLayout(orientation="vertical", spacing=8, padding=10)
        ti = TextInput(hint_text="اسم المجلد الجديد", multiline=False)
        content.add_widget(ti)
        row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        popup = Popup(title="مجلد جديد", content=content, size_hint=(0.85, 0.35))

        def confirm(_):
            try:
                file_ops.create_folder(self.current_path, ti.text)
                self.refresh()
            except OSError as e:
                self._toast(str(e))
            popup.dismiss()

        row.add_widget(Button(text="إنشاء", on_release=confirm))
        row.add_widget(Button(text="إلغاء", on_release=popup.dismiss))
        content.add_widget(row)
        popup.open()

    def new_file_popup(self):
        content = BoxLayout(orientation="vertical", spacing=8, padding=10)
        ti = TextInput(hint_text="اسم الملف (مثال: ملاحظة.txt)", multiline=False)
        content.add_widget(ti)
        row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        popup = Popup(title="ملف نصي جديد", content=content, size_hint=(0.85, 0.35))

        def confirm(_):
            try:
                file_ops.create_text_file(self.current_path, ti.text)
                self.refresh()
            except OSError as e:
                self._toast(str(e))
            popup.dismiss()

        row.add_widget(Button(text="إنشاء", on_release=confirm))
        row.add_widget(Button(text="إلغاء", on_release=popup.dismiss))
        content.add_widget(row)
        popup.open()

    def open_menu(self):
        from kivy.metrics import dp
        popup = Popup(title="قائمة", size_hint=(0.8, 0.6))
        box = BoxLayout(orientation="vertical", spacing=6, padding=8)
        actions = [
            ("مجلد جديد", self.new_folder_popup),
            ("ملف نصي جديد", self.new_file_popup),
            ("لصق", self.paste_here),
        ]
        for label, fn in actions:
            btn = Button(text=label, size_hint_y=None, height=dp(46))

            def make_cb(f=fn):
                def cb(instance):
                    popup.dismiss()
                    f()
                return cb
            btn.bind(on_release=make_cb())
            box.add_widget(btn)
        popup.content = box
        popup.open()

    def go_favorites(self):
        App.get_running_app().sm.current = "favorites"

    def go_trash(self):
        App.get_running_app().sm.current = "trash"

    def go_duplicates(self):
        App.get_running_app().sm.current = "duplicates"

    def go_settings(self):
        App.get_running_app().sm.current = "settings"

    def go_about(self):
        App.get_running_app().sm.current = "about"

    def _toast(self, msg):
        popup = Popup(title="", content=Label(text=msg), size_hint=(0.7, 0.2))
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.4)


class TrashScreen(Screen):
    def on_pre_enter(self):
        self.refresh()

    def refresh(self):
        from kivy.metrics import dp
        box = self.ids.trash_list
        box.clear_widgets()
        items = file_ops.list_trash(storage_utils.get_storage_root())
        for item in items:
            row = BoxLayout(size_hint_y=None, height=dp(52), spacing=6, padding=6)
            row.add_widget(Label(text=item["original_name"]))
            restore_btn = Button(text="استعادة", size_hint_x=0.3)
            restore_btn.bind(on_release=lambda b, p=item["path"]: self._restore(p))
            del_btn = Button(text="حذف نهائي", size_hint_x=0.3)
            del_btn.bind(on_release=lambda b, p=item["path"]: self._delete(p))
            row.add_widget(restore_btn)
            row.add_widget(del_btn)
            box.add_widget(row)

    def _restore(self, path):
        browser = App.get_running_app().sm.get_screen("browser")
        file_ops.restore_from_trash(path, browser.current_path)
        self.refresh()

    def _delete(self, path):
        file_ops.permanent_delete(path)
        self.refresh()

    def empty_all(self):
        file_ops.empty_trash(storage_utils.get_storage_root())
        self.refresh()

    def go_back(self):
        App.get_running_app().sm.current = "browser"


class FavoritesScreen(Screen):
    def on_pre_enter(self):
        self.refresh()

    def refresh(self):
        from kivy.metrics import dp
        box = self.ids.fav_list
        box.clear_widgets()
        app = App.get_running_app()
        favs = app.config_data.get("favorites", [])
        for path in list(favs):
            row = BoxLayout(size_hint_y=None, height=dp(52), spacing=6, padding=6)
            exists = os.path.exists(path)
            label_text = os.path.basename(path) + ("" if exists else " (مفقود)")
            row.add_widget(Label(text=label_text))
            if exists:
                open_btn = Button(text="فتح", size_hint_x=0.25)
                open_btn.bind(on_release=lambda b, p=path: self._open(p))
                row.add_widget(open_btn)
            rm_btn = Button(text="إزالة", size_hint_x=0.25)
            rm_btn.bind(on_release=lambda b, p=path: self._remove(p))
            row.add_widget(rm_btn)
            box.add_widget(row)

    def _open(self, path):
        browser = App.get_running_app().sm.get_screen("browser")
        if os.path.isdir(path):
            browser.current_path = path
        else:
            browser.current_path = os.path.dirname(path)
        App.get_running_app().sm.current = "browser"

    def _remove(self, path):
        app = App.get_running_app()
        favs = app.config_data.get("favorites", [])
        if path in favs:
            favs.remove(path)
            crypto_utils.save_config(app.config_data)
        self.refresh()

    def go_back(self):
        App.get_running_app().sm.current = "browser"


class DuplicatesScreen(Screen):
    def scan(self):
        from kivy.metrics import dp
        box = self.ids.dup_list
        box.clear_widgets()
        root = storage_utils.get_storage_root()
        groups = file_ops.find_duplicates(root)
        if not groups:
            box.add_widget(Label(text="لا يوجد تكرار", size_hint_y=None, height=dp(44)))
            return
        for group in groups:
            header = Label(text=f"مجموعة ({len(group)} ملفات متطابقة)",
                            size_hint_y=None, height=dp(30), color=(0.6, 0.8, 1, 1))
            box.add_widget(header)
            for path in group:
                row = BoxLayout(size_hint_y=None, height=dp(44), spacing=6, padding=6)
                row.add_widget(Label(text=os.path.basename(path), shorten=True))
                del_btn = Button(text="حذف", size_hint_x=0.3)
                del_btn.bind(on_release=lambda b, p=path: self._delete(p))
                row.add_widget(del_btn)
                box.add_widget(row)

    def _delete(self, path):
        try:
            file_ops.move_to_trash(path, storage_utils.get_storage_root())
        except OSError:
            pass
        self.scan()

    def go_back(self):
        App.get_running_app().sm.current = "browser"


class SettingsScreen(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        self.ids.hidden_switch.active = app.config_data.get("show_hidden", False)
        usage = file_ops.disk_usage(storage_utils.get_storage_root())
        self.ids.storage_info.text = (
            f"المساحة الكلية: {usage['total_h']}\n"
            f"المستخدم: {usage['used_h']}\n"
            f"المتاح: {usage['free_h']}"
        )

    def toggle_hidden(self, active):
        app = App.get_running_app()
        app.config_data["show_hidden"] = active
        crypto_utils.save_config(app.config_data)

    def change_password_popup(self):
        content = BoxLayout(orientation="vertical", spacing=8, padding=10)
        old_pw = TextInput(hint_text="كلمة السر الحالية", password=True, multiline=False)
        new_pw = TextInput(hint_text="كلمة السر الجديدة", password=True, multiline=False)
        content.add_widget(old_pw)
        content.add_widget(new_pw)
        row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        popup = Popup(title="تغيير كلمة السر", content=content, size_hint=(0.85, 0.5))

        def confirm(_):
            if crypto_utils.verify_master_password(old_pw.text) and new_pw.text:
                crypto_utils.set_master_password(new_pw.text)
            popup.dismiss()

        row.add_widget(Button(text="تأكيد", on_release=confirm))
        row.add_widget(Button(text="إلغاء", on_release=popup.dismiss))
        content.add_widget(row)
        popup.open()

    def go_back(self):
        App.get_running_app().sm.current = "browser"


class AboutScreen(Screen):
    def go_back(self):
        App.get_running_app().sm.current = "browser"


class TextEditorScreen(Screen):
    file_path = StringProperty("")
    file_name = StringProperty("")

    def load_file(self, path):
        self.file_path = path
        self.file_name = os.path.basename(path)
        try:
            content = file_ops.read_text_file(path)
        except OSError:
            content = ""
        self.ids.editor_input.text = content

    def save(self):
        try:
            file_ops.write_text_file(self.file_path, self.ids.editor_input.text)
        except OSError:
            pass
        App.get_running_app().sm.current = "browser"

    def cancel(self):
        App.get_running_app().sm.current = "browser"


class FileManagerApp(App):
    config_data = {}
    has_arabic_font = BooleanProperty(False)

    def build(self):
        self.title = APP_TITLE
        self.config_data = crypto_utils.load_config()
        Builder.load_string(KV)
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(LockScreen(name="lock"))
        self.sm.add_widget(BrowserScreen(name="browser"))
        self.sm.add_widget(TrashScreen(name="trash"))
        self.sm.add_widget(FavoritesScreen(name="favorites"))
        self.sm.add_widget(DuplicatesScreen(name="duplicates"))
        self.sm.add_widget(SettingsScreen(name="settings"))
        self.sm.add_widget(AboutScreen(name="about"))
        self.sm.add_widget(TextEditorScreen(name="editor"))
        Clock.schedule_once(lambda dt: self._request_permissions(), 0.5)
        return self.sm

    def _request_permissions(self):
        storage_utils.request_storage_permissions(callback=lambda ok: None)


if __name__ == "__main__":
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    FileManagerApp().run()
else:
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
