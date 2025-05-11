import pyxel
import csv
import random
import os

IMAGE_BANK_BACKGROUND = 2

def draw_text_with_border(x, y, s, col, bcol, font):
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx != 0 or dy != 0:
                if font:
                    pyxel.text(x + dx, y + dy, s, bcol, font)
                else:
                    pyxel.text(x + dx, y + dy, s, bcol)

    if font:
        pyxel.text(x, y, s, col, font)
    else:
        pyxel.text(x, y, s, col)

class WordBookApp:
    CSV_FILENAME = "word.csv"

    def __init__(self):
        self.screen_width = 220
        self.screen_height = 180
        pyxel.init(self.screen_width, self.screen_height, title="英単語帳 (Pyxel Wordbook)")

        try:
            self.custom_font = pyxel.Font("assets/umplus_j12r.bdf")
            print("カスタムフォント 'assets/umplus_j12r.bdf' を読み込みました。")
        except RuntimeError as e:
            print(f"カスタムフォントの読み込みに失敗: {e}")
            print("Pyxelのシステムフォントを使用します。")
            self.custom_font = None

        self.words = self.load_words_from_csv(WordBookApp.CSV_FILENAME)

        if not self.words:
            print(f"警告: 単語ファイル '{WordBookApp.CSV_FILENAME}' の読み込みに失敗したか、単語が含まれていません。")
            self.current_word_index = -1
        else:
            self.current_word_index = 0
        
        self.show_meaning = False

        self.background_image_files = [f"{i:02d}.png" for i in range(1, 11)]
        self.selected_bg_image_file = None
        self.background_loaded = False
        self.default_bg_color = pyxel.COLOR_GRAY
        self._load_random_background()

        self.button_height = 18
        self.button_margin = 10
        
        button_width_prev_next = 70
        self.prev_button_rect = (
            self.button_margin,
            self.screen_height - self.button_height - self.button_margin,
            button_width_prev_next,
            self.button_height
        )
        self.next_button_rect = (
            self.screen_width - button_width_prev_next - self.button_margin,
            self.screen_height - self.button_height - self.button_margin,
            button_width_prev_next,
            self.button_height
        )
        
        button_width_toggle = 90
        self.toggle_meaning_button_rect = (
            (self.screen_width - button_width_toggle) // 2,
            self.screen_height - self.button_height - self.button_margin,
            button_width_toggle,
            self.button_height
        )
        
        self.text_color = pyxel.COLOR_WHITE
        self.border_color = pyxel.COLOR_NAVY
        self.button_color = pyxel.COLOR_PURPLE
        self.button_text_color = pyxel.COLOR_WHITE
        self.button_border_color = pyxel.COLOR_BLACK

        pyxel.run(self.update, self.draw)

    def _load_random_background(self):
        available_images = [f for f in self.background_image_files if os.path.exists(f)]

        if not available_images:
            if not self.background_loaded:
                print("利用可能な背景画像ファイルがカレントディレクトリに見つかりませんでした。")
            self.background_loaded = False
            return

        self.selected_bg_image_file = random.choice(available_images)

        try:
            pyxel.image(IMAGE_BANK_BACKGROUND).load(0, 0, self.selected_bg_image_file)
            self.background_loaded = True
        except RuntimeError as e:
            print(f"エラー: 背景画像 '{self.selected_bg_image_file}' のロードに失敗しました: {e}")
            self.background_loaded = False
        except Exception as e:
            print(f"予期せぬエラー: 背景画像 '{self.selected_bg_image_file}' のロード中に問題が発生しました: {e}")
            self.background_loaded = False

    def load_words_from_csv(self, filename):
        words_list = []
        try:
            with open(filename, mode='r', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                for i, row in enumerate(reader):
                    if len(row) == 2:
                        english_word = row[0].strip()
                        japanese_translation = row[1].strip()
                        if english_word and japanese_translation:
                             words_list.append({"english": english_word, "japanese": japanese_translation})
                        else:
                            print(f"警告: スキップされた行 {i+1} (空の単語または訳): {row} in {filename}")
                    elif row:
                        print(f"警告: スキップされた行 {i+1} (不正な形式、要素数 {len(row)}): {row} in {filename}")
        except FileNotFoundError:
            print(f"エラー: 単語ファイル '{filename}' が見つかりません。")
        except Exception as e:
            print(f"エラー: 単語ファイル '{filename}' の読み込み中にエラーが発生しました: {e}")
        
        if words_list:
            print(f"{len(words_list)}語の単語を '{filename}' から読み込みました。")
        return words_list

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        
        if not self.words:
            return

        # --- 入力処理の統合 ---
        # 単語を前へ
        prev_pressed = (
            pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_C) or
            pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X)
        )

        # 単語を次へ
        next_pressed = (
            pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D) or pyxel.btnp(pyxel.KEY_X) or
            pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)
        )

        # 意味の表示/非表示
        toggle_meaning_pressed = (
            pyxel.btnp(pyxel.KEY_Z) or
            pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)
        )

        if prev_pressed:
            self.go_to_prev_word()
        elif next_pressed: # elif を使用して同時押しによる連続動作を防ぐ
            self.go_to_next_word()
        
        if toggle_meaning_pressed:
            self.toggle_show_meaning()
        # --- 入力処理ここまで ---


    def go_to_prev_word(self):
        if not self.words: return
        if self.current_word_index > 0:
            self.current_word_index -= 1
        else:
            self.current_word_index = len(self.words) -1
        self.show_meaning = False
        self._load_random_background()

    def go_to_next_word(self):
        if not self.words: return
        if self.current_word_index < len(self.words) - 1:
            self.current_word_index += 1
        else:
            self.current_word_index = 0
        self.show_meaning = False
        self._load_random_background()
            
    def toggle_show_meaning(self):
        if not self.words: return
        self.show_meaning = not self.show_meaning

    def draw_centered_text(self, y, text, color, border_color, font_to_use):
        if font_to_use:
            text_width = font_to_use.text_width(text)
        else:
            text_width = len(text) * pyxel.FONT_WIDTH
        
        x = (self.screen_width - text_width) // 2
        draw_text_with_border(x, y, text, color, border_color, font_to_use)

    def draw_button(self, rect, text, font_to_use=None):
        x, y, w, h = rect
        pyxel.rect(x, y, w, h, self.button_color)
        
        if font_to_use:
            text_w = font_to_use.text_width(text)
            text_h = font_to_use.height 
        else:
            text_w = len(text) * pyxel.FONT_WIDTH
            text_h = pyxel.FONT_HEIGHT
        
        text_x = x + (w - text_w) // 2
        text_y = y + (h - text_h) // 2 
        
        draw_text_with_border(text_x, text_y, text, self.button_text_color, self.button_border_color, font_to_use)

    def draw(self):
        pyxel.cls(self.default_bg_color)

        if self.background_loaded:
            img = pyxel.image(IMAGE_BANK_BACKGROUND)
            img_w = img.width
            img_h = img.height
            draw_x = (self.screen_width - img_w) // 2
            draw_y = (self.screen_height - img_h) // 2
            pyxel.blt(draw_x, draw_y, IMAGE_BANK_BACKGROUND, 0, 0, img_w, img_h)

        if not self.words:
            message_lines = [
                f"'{WordBookApp.CSV_FILENAME}'が見つからないか",
                "有効な単語がありません。",
                " ",
                "Q: Quit"
            ]
            text_y = self.screen_height // 2 - (len(message_lines) * (pyxel.FONT_HEIGHT + 2)) // 2
            for line in message_lines:
                msg_w = len(line) * pyxel.FONT_WIDTH
                draw_text_with_border(
                    (self.screen_width - msg_w) // 2,
                    text_y,
                    line,
                    self.text_color,
                    self.border_color,
                    None
                )
                text_y += pyxel.FONT_HEIGHT + 2
            return

        current_word_data = self.words[self.current_word_index]
        english_word = current_word_data["english"]
        japanese_meaning = current_word_data["japanese"]

        self.draw_centered_text(40, english_word, self.text_color, self.border_color, self.custom_font)

        if self.show_meaning:
            self.draw_centered_text(80, japanese_meaning, self.text_color, self.border_color, self.custom_font)
        else:
            self.draw_centered_text(80, "**********", self.text_color, self.border_color, self.custom_font)

        self.draw_button(self.prev_button_rect, "Prev (C/XBtn)") # キーヒントを少し更新
        self.draw_button(self.next_button_rect, "Next (X/BBtn)")
        
        toggle_btn_text = "Show (Z/ABtn)" if not self.show_meaning else "Hide (Z/ABtn)"
        self.draw_button(self.toggle_meaning_button_rect, toggle_btn_text)

        progress_text = f"{self.current_word_index + 1} / {len(self.words)}"
        progress_text_w = len(progress_text) * pyxel.FONT_WIDTH
        draw_text_with_border(
            (self.screen_width - progress_text_w) // 2, 
            self.button_margin, 
            progress_text, 
            self.text_color, 
            self.border_color, 
            None
        )
        
        instruction_y_base = self.screen_height - self.button_height - self.button_margin - 10
        line_height = pyxel.FONT_HEIGHT + 2

        instruction_text1 = "L/R or C/X (Key) | D-Pad L/R or X (Pad): Word"
        instruction_text2 = "Z (Key) | A or D-Pad Down (Pad): Meaning"
        instruction_text3 = "Q (Key): Quit"
        
        # 画面幅に合わせて説明文を調整、必要なら2行に
        inst_text_w1 = len(instruction_text1) * pyxel.FONT_WIDTH
        if inst_text_w1 > self.screen_width - 10: # 画面幅を超えるようなら簡略化
            instruction_text1 = "Arrows/C/X | D-Pad/XBtn: Word"
            inst_text_w1 = len(instruction_text1) * pyxel.FONT_WIDTH
        
        draw_text_with_border(
            (self.screen_width - inst_text_w1) // 2, 
            instruction_y_base - line_height * 2, 
            instruction_text1, 
            pyxel.COLOR_LIME, pyxel.COLOR_BLACK, 
            None
        )
        
        inst_text_w2 = len(instruction_text2) * pyxel.FONT_WIDTH
        if inst_text_w2 > self.screen_width - 10:
            instruction_text2 = "Z | ABtn/D-Down: Meaning"
            inst_text_w2 = len(instruction_text2) * pyxel.FONT_WIDTH

        draw_text_with_border(
            (self.screen_width - inst_text_w2) // 2, 
            instruction_y_base - line_height, 
            instruction_text2, 
            pyxel.COLOR_LIME, pyxel.COLOR_BLACK, 
            None
        )
        
        inst_text_w3 = len(instruction_text3) * pyxel.FONT_WIDTH
        draw_text_with_border(
            (self.screen_width - inst_text_w3) // 2, 
            instruction_y_base, 
            instruction_text3, 
            pyxel.COLOR_LIME, pyxel.COLOR_BLACK, 
            None
        )

if __name__ == '__main__':
    print("英単語帳アプリ (Pyxel Wordbook)")
    print("------------------------------------")
    print(f"単語データを '{WordBookApp.CSV_FILENAME}' から読み込みます。")
    print("背景画像をカレントディレクトリの '01.png'～'10.png' からランダムに読み込み、")
    print("単語を切り替えるたびに背景もランダムに変わります。")
    print("操作方法 (キーボード | ゲームパッド):")
    print(" - 単語を前へ: ←/A/C キー | DPAD LEFT / Xボタン")
    print(" - 単語を次へ: →/D/X キー | DPAD RIGHT / Bボタン")
    print(" - 意味表示/非表示: Z キー | Aボタン / DPAD DOWN")
    print(" - 終了: Q キー")
    print("------------------------------------")
    print("カスタムフォント 'assets/umplus_j12r.bdf' があれば使用されます。")
    print("ない場合はPyxelのシステムフォントが使用されます。")
    print("------------------------------------")
    WordBookApp()