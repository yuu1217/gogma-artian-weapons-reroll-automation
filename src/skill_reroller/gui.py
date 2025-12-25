import flet as ft
import threading
import logging
import sys
import toml
from pathlib import Path
from datetime import datetime
from .config import (
    SERIES_SKILLS,
    GROUP_SKILLS,
    OUTPUT_DIR,
    MAX_ATTEMPTS,
    STOP_ON_MATCH,
    RETURN_TO_TITLE,
)
from .game_logic import GameLogic


def setup_logging(timestamp: str):
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / f"{timestamp}.txt", encoding="utf-8"),
        ],
    )


def create_app(page: ft.Page):
    page.title = "巨戟アーティア武器スキル厳選自動化ツール"
    page.window.width = 720
    page.window.height = 960
    page.window.min_width = 720
    page.window.min_height = 320
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.AMBER)
    page.padding = 20

    def get_directory_result(e):
        if e.path:
            output_path.value = e.path
            output_path.update()

    get_directory_dialog = ft.FilePicker()
    get_directory_dialog.on_result = get_directory_result
    page.overlay.append(get_directory_dialog)

    output_path = ft.TextField(
        label="出力フォルダー",
        value=OUTPUT_DIR,
        read_only=False,
        expand=True,
        border_color=ft.Colors.GREY_500,
        label_style=ft.TextStyle(color=ft.Colors.GREY_500),
    )

    folder_picker_button = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: get_directory_dialog.get_directory_path(),
    )

    path_row = ft.Row(
        [output_path, folder_picker_button],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    skill_sets = []

    max_attempts_input = ft.TextField(
        label="スキル再付与を行う回数 (0は素材を使い切るまで)",
        value=str(MAX_ATTEMPTS),
        expand=True,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(
            allow=True, regex_string=r"^\d*$", replacement_string=""
        ),
        text_align=ft.TextAlign.RIGHT,
        border_color=ft.Colors.GREY_500,
        label_style=ft.TextStyle(color=ft.Colors.GREY_500),
    )

    return_title_checkbox = ft.Checkbox(
        label="終了後セーブせずタイトルに戻る",
        value=RETURN_TO_TITLE,
        expand=True,
    )

    stop_match_checkbox = ft.Checkbox(
        label="当たりが出たら停止",
        value=STOP_ON_MATCH,
        expand=True,
    )

    # configから初期値を反映
    from .config import TARGET_COMBINATIONS

    for i in range(5):
        init_series = None
        init_group = None
        if i < len(TARGET_COMBINATIONS):
            combo = TARGET_COMBINATIONS[i]
            if len(combo) >= 1:
                init_series = combo[0]
            if len(combo) >= 2:
                init_group = combo[1]

        series_skill = ft.Dropdown(
            hint_text="シリーズスキル",
            options=[ft.dropdown.Option(skill) for skill in SERIES_SKILLS],
            value=init_series,
            expand=True,
            border_color=ft.Colors.GREY_500,
            hint_style=ft.TextStyle(color=ft.Colors.GREY_500),
        )
        group_skill = ft.Dropdown(
            hint_text="グループスキル",
            options=[ft.dropdown.Option(skill) for skill in GROUP_SKILLS],
            value=init_group,
            expand=True,
            border_color=ft.Colors.GREY_500,
            hint_style=ft.TextStyle(color=ft.Colors.GREY_500),
        )
        skill_sets.append((series_skill, group_skill))

    run_button = ft.Button(
        "厳選開始",
        icon=ft.Icons.PLAY_ARROW,
        style=ft.ButtonStyle(
            color=ft.Colors.ON_PRIMARY,
            bgcolor=ft.Colors.PRIMARY,
            padding=20,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        height=50,
        width=200,
        disabled=False,
    )

    def show_error(message: str):
        page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=ft.Colors.RED)
        page.snack_bar.open = True
        page.update()

    def save_settings():
        try:
            config_path = Path("src/skill_reroller/config.toml")
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = toml.load(f)

            # 設定を更新
            config_data["output"]["dir"] = output_path.value

            # ターゲットの組み合わせを更新 (空欄は除外)
            new_target_combinations = []
            for series_skill, group_skill in skill_sets:
                # いずれかが設定されている場合のみ保存対象とする
                if series_skill.value or group_skill.value:
                    s_val = series_skill.value if series_skill.value else ""
                    g_val = group_skill.value if group_skill.value else ""
                    new_target_combinations.append([s_val, g_val])

            # リロール設定を更新
            try:
                max_attempts_val = int(max_attempts_input.value)
            except ValueError:
                max_attempts_val = 0

            config_data["reroll"]["max_attempts"] = max_attempts_val
            config_data["reroll"]["stop_on_match"] = stop_match_checkbox.value
            config_data["reroll"]["return_to_title"] = return_title_checkbox.value

            config_data["reroll"]["target_combinations"] = new_target_combinations

            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(config_data, f)

            logging.getLogger(__name__).info("Settings saved to config.toml")

        except Exception as e:
            error_msg = f"設定の保存に失敗しました: {e}"
            logging.getLogger(__name__).error(error_msg)
            show_error(error_msg)

    def on_run_click(e):
        # 二重起動防止とボタン表示変更
        run_button.text = "Alt+Qで停止"
        run_button.icon = ft.Icons.STOP
        run_button.style.bgcolor = ft.Colors.GREY_700
        run_button.disabled = True
        page.update()

        save_settings()

        # 別スレッドで実行 (GUIフリーズ防止)
        def run_game():
            try:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                setup_logging(timestamp)
                logger = logging.getLogger(__name__)

                # 空でないスキルセットを収集
                target_combos = []
                for series_skill, group_skill in skill_sets:
                    if series_skill.value or group_skill.value:
                        s_val = series_skill.value if series_skill.value else ""
                        g_val = group_skill.value if group_skill.value else ""
                        target_combos.append([s_val, g_val])

                if not target_combos:
                    msg = "スキル組み合わせが選択されていません"
                    logger.warning(msg)
                    show_error(msg)
                    return

                logger.info("Starting Artian Weapon Reroll Automation Tool")
                logger.info(f"Target combinations: {target_combos}")

                # GameLogicを実行
                game = GameLogic(
                    max_attempts=(
                        int(max_attempts_input.value)
                        if max_attempts_input.value.isdigit()
                        else 0
                    ),
                    timestamp=timestamp,
                    target_combination=target_combos,
                    stop_on_match=stop_match_checkbox.value,
                    return_to_title=return_title_checkbox.value,
                )
                game.run()

                logger.info("Tool finished.")

            except Exception as ex:
                logger = logging.getLogger(__name__)
                logger.critical(f"Unhandled exception: {ex}", exc_info=True)
                show_error(f"エラーが発生しました: {ex}")
            finally:
                run_button.text = "厳選開始"
                run_button.icon = ft.Icons.PLAY_ARROW
                run_button.style.bgcolor = ft.Colors.PRIMARY
                run_button.disabled = False
                page.update()

        thread = threading.Thread(target=run_game, daemon=True)
        thread.start()

    run_button.on_click = on_run_click

    skill_sections = []
    for i, (series_skill, group_skill) in enumerate(skill_sets):
        skill_sections.append(
            ft.Column(
                [
                    ft.Text(f"組み合わせ {i+1}", size=14, weight=ft.FontWeight.BOLD),
                    ft.Row([series_skill, group_skill], spacing=10),
                ]
            )
        )

    # レイアウト構築

    # 出力設定
    path_section = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "出力設定",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PRIMARY,
                ),
                path_row,
            ],
            spacing=15,
        ),
        padding=15,
        bgcolor=ft.Colors.GREY_900,
        border_radius=10,
    )

    # 実行オプション
    options_section = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "実行オプション",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PRIMARY,
                ),
                ft.Row([max_attempts_input], alignment=ft.MainAxisAlignment.START),
                ft.Row(
                    [return_title_checkbox, stop_match_checkbox],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=15,
                ),
            ],
            spacing=15,
        ),
        padding=15,
        bgcolor=ft.Colors.GREY_900,
        border_radius=10,
    )

    # ターゲットスキル
    skill_controls = []
    for section in skill_sections:
        skill_controls.append(section)
        skill_controls.append(ft.Divider(height=10, color=ft.Colors.GREY_700))

    # 最後のDividerを削除
    if skill_controls:
        skill_controls.pop()

    skills_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "狙いたいスキルの組み合わせ",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY,
                    ),
                    ft.Text(
                        "※シリーズ・グループのいずれか片方のみも可",
                        size=12,
                        color=ft.Colors.GREY_500,
                    ),
                    ft.Divider(),
                    *skill_controls,
                ],
                spacing=15,
            ),
            padding=20,
        ),
        elevation=2,
    )

    # 説明欄
    description_container = ft.Container(
        content=ft.Markdown(
            """
### 説明

ワイルズの巨戟アーティア武器は、各武器の各属性ごとにスキルの組み合わせの出る順番が決まっていて、セーブ&ロードでやり直しても同じ結果になります。この仕様を利用し、自動で繰り返し再付与を行い何回目で欲しいスキルの組み合わせが出るのかを確認できるツールです。表と組み合わせて使うとより効率的です。 (ここでは表を使った厳選方法は説明しません。)

1. ゲーム画面をウィンドウモードかウィンドウフルスクリーンで起動してスキル再付与の画面を表示してください。
2. 各種設定を確認し実行してください。当てたいスキルの組み合わせは5つまで設定できます。
3. 自動でスキル再付与を繰り返し、設定したスキルの組み合わせが出たら回数とスクリーンショットを保存します。
4. 再付与が終わるとセーブせずにタイトルに戻ります。また厳選の履歴をまとめたレポートを保存します。
5. お目当ての組み合わせが出ていた場合は、その回数まで再付与をもう一度行うことでその組み合わせを再現できます。お手元の厳選表に記録したり、改めて再付与して入手してください。

### 備考

- 途中で停止した場合もレポートは保存されます。
- スキルの組み合わせはシリーズスキルかグループスキルのどちらか一方のみの設定でも問題ありません。
- 所持している素材分で抽選できる回数以上を指定した場合は、所持している素材分抽選しきった段階で終了します。
- 「当たりが出たら停止」をチェックしておけば、設定したスキルの組み合わせが出たらそこで停止します。スキルを実際に付与するかどうかの確認画面で終了します。
- 「終了後セーブせずタイトルに戻る」のチェックを外すとタイトルに戻りません。

### 本ツールを作った理由

狩りの時間より拠点でガチャ回してる時間の方が長いってどうなの…我々はハンティングアクションゲームをやりたかったはずでは…
""",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
            on_tap_link=lambda e: page.launch_url(e.data),
        ),
        padding=15,
        border=ft.border.all(1, ft.Colors.GREY_700),
        border_radius=10,
    )

    # ListViewを使用してスクロール機能とPaddingを両立
    list_view = ft.ListView(
        controls=[
            path_section,
            ft.Divider(height=10, color="transparent"),
            options_section,
            ft.Divider(height=20, color="transparent"),
            skills_card,
            ft.Divider(height=30, color="transparent"),
            ft.Row([run_button], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(height=30, color="transparent"),
            description_container,
            ft.Divider(height=50, color="transparent"),
        ],
        spacing=0,
        padding=30,
        expand=True,
    )

    main_container = ft.Container(
        content=list_view,
        width=600,
        padding=20,
        alignment=ft.alignment.top_center,
    )

    page.add(
        ft.Row(
            [main_container],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )
    )

    page.padding = 0
