import flet as ft
from src.skill_reroller import create_app

if __name__ == "__main__":
    ft.app(create_app)

# 今はスキルリローラーしかないので直接起動する。もし今後ボーナスリローラーも作った場合は、src直下に2つのツールをまとめるファイル用意してそこから各ツールのページにつなぐ。
