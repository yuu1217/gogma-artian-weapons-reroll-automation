import flet as ft
import threading
import logging
import sys
import toml
import os
from pathlib import Path
from datetime import datetime
from .config import (
    SERIES_SKILLS,
    GROUP_SKILLS,
    OUTPUT_DIR,
    MAX_ATTEMPTS,
    STOP_ON_MATCH,
    RETURN_TO_TITLE,
    WEAPONS,
    ELEMENTS,
    LAST_WEAPON,
    LAST_ELEMENT,
    CURRENT_CONFIRMED_COUNT,
    MATCH_THRESHOLD,
)
from .game_logic import GameLogic
from .table_manager import TableManager  # インポート追加


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
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.AMBER)
    page.padding = 20

    # ウィンドウサイズ設定
    page.window.width = 720
    page.window.height = 960
    page.window.min_width = 720
    page.window.min_height = 320
    page.window.max_width = 960
    page.window.max_height = 2160

    table_manager = TableManager()  # TableManagerの初期化

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
    )

    folder_picker_button = ft.IconButton(
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: get_directory_dialog.get_directory_path(),
    )

    path_row = ft.Row(
        [output_path, folder_picker_button],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # --- 武器選択セクション ---
    weapon_dropdown = ft.Dropdown(
        label="武器種",
        options=[ft.dropdown.Option(w) for w in WEAPONS],
        value=(
            LAST_WEAPON if LAST_WEAPON in WEAPONS else (WEAPONS[0] if WEAPONS else None)
        ),
        expand=True,
        border_color=ft.Colors.GREY_500,
    )

    element_dropdown = ft.Dropdown(
        label="属性",
        options=[ft.dropdown.Option(e) for e in ELEMENTS],
        value=(
            LAST_ELEMENT
            if LAST_ELEMENT in ELEMENTS
            else (ELEMENTS[0] if ELEMENTS else None)
        ),
        expand=True,
        border_color=ft.Colors.GREY_500,
    )

    confirmed_count_input = ft.TextField(
        label="確定済み回数",
        value=str(CURRENT_CONFIRMED_COUNT),
        expand=True,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(
            allow=True, regex_string=r"^\d*$", replacement_string=""
        ),
        text_align=ft.TextAlign.RIGHT,
        border_color=ft.Colors.GREY_500,
    )

    reload_table_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="厳選表を再読み込み",
        on_click=lambda e: reload_table_action(e),
    )

    def reload_table_action(e):
        # TableManagerのデータを再読み込み
        table_manager.data.clear()
        table_manager.headers = ["回数"]
        table_manager.load_table()

        page.snack_bar = ft.SnackBar(
            ft.Text("厳選表を再読み込みしました"),
            bgcolor=ft.Colors.GREEN,
        )
        page.snack_bar.open = True
        page.update()

    selection_row = ft.Row(
        [weapon_dropdown, element_dropdown],
        spacing=10,
    )

    confirmed_count_row = ft.Row(
        [confirmed_count_input],
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
        expand=True,
        disabled=False,
    )

    route_button = ft.ElevatedButton(
        text="厳選ルート",
        icon=ft.Icons.ROUTE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=20,
        ),
        expand=True,
        on_click=lambda _: page.go("/routes"),
    )

    def open_output_folder(e):
        path = output_path.value
        if path:
            # 相対パスを絶対パスに変換
            abs_path = Path(path).resolve()
            if abs_path.exists():
                os.startfile(str(abs_path))
            else:
                show_error("フォルダが見つかりません。")
        else:
            show_error("フォルダが指定されていません。")

    open_folder_button = ft.ElevatedButton(
        text="厳選表の場所",
        icon=ft.Icons.FOLDER_OPEN,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=20,
        ),
        expand=True,
        on_click=open_output_folder,
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

            try:
                confirmed_cnt = int(confirmed_count_input.value)
            except ValueError:
                confirmed_cnt = 0
            config_data["reroll"]["current_confirmed_count"] = confirmed_cnt

            config_data["reroll"]["target_combinations"] = new_target_combinations

            # 前回選択値を保存
            if "selection" not in config_data:
                config_data["selection"] = {}

            config_data["selection"]["last_weapon"] = weapon_dropdown.value
            config_data["selection"]["last_element"] = element_dropdown.value

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
                    weapon_name=weapon_dropdown.value,  # 新規引数
                    weapon_element=element_dropdown.value,  # 新規引数
                    confirmed_count=(
                        int(confirmed_count_input.value)
                        if confirmed_count_input.value.isdigit()
                        else 0
                    ),  # 新規引数
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

    # 実行オプション
    options_section_content = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "実行オプション",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PRIMARY,
                ),
                path_row,  # 移動
                ft.Divider(height=1),  # 追加
                selection_row,
                ft.Row([max_attempts_input], alignment=ft.MainAxisAlignment.START),
                ft.Row(
                    [return_title_checkbox, stop_match_checkbox],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=15,
                ),
                ft.Divider(height=1),  # 追加
                confirmed_count_row,
                ft.Text(  # 内容修正
                    "セーブされており、確定している回数です。ロードし直してもこれ以上戻れないポイントとも言えます。厳選表を使用しない場合は変更の必要はありません。",
                    size=12,
                    color=ft.Colors.GREY_500,
                ),
            ],
            spacing=15,
        ),
        padding=20,
    )

    options_section = ft.Card(
        content=options_section_content,
        elevation=2,
    )

    # ターゲットスキル
    skill_controls = []
    for section in skill_sections:
        skill_controls.append(section)
        # Dividerは削除

    skills_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "付与したいスキルの組み合わせ",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PRIMARY,
                    ),
                    ft.Text(
                        "シリーズとグループのいずれか片方のみも可",
                        size=12,
                        color=ft.Colors.GREY_500,
                    ),
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

ワイルズの巨戟アーティア武器は、各武器の各属性ごとにスキルの組み合わせの出る順番が決まっていて、セーブ&ロードでやり直しても同じ結果になります。この仕様を利用し、自動で繰り返し再付与を行い何回目で欲しいスキルの組み合わせが出るのかを確認できるツールです。表と組み合わせて使うとより効率的です。

1. ゲーム画面をウィンドウモードかウィンドウフルスクリーンモードで起動してスキル再付与の画面を表示してください。
2. 各種設定を確認し実行してください。当てたいスキルの組み合わせは5つまで設定できます。
3. 自動でスキル再付与を繰り返し、設定したスキルの組み合わせが出たら回数とスクリーンショットを保存します。
4. 再付与が終わるとセーブせずにタイトルに戻ります。また厳選の履歴をまとめたレポートを保存と厳選表の更新を行います。
5. お目当ての組み合わせが出ていた場合は、その回数まで再付与をもう一度行うことでその組み合わせを再現できます。

#### 厳選表

本ツールで厳選を実行すると`reroll_table.csv`というファイルが設定したフォルダーに自動で作成、更新されます。これは各武器各属性において「何回目にどのスキルの組み合わせが出たか」を記録した表、いわゆる厳選表です。ExcelやGoogle スプレッドシートなどで開けます。またこの表から導出した「何回目にどの武器にスキル付与すればよいか」を「厳選ルート」ボタンから確認できます。

なお表の更新時には「確定済み回数」より後のデータのみを更新します。ゲーム内で厳選後セーブを行って結果を確定させた回数をここに入力してください。例えば、厳選を開始して10回目に狙いたいスキルが出てセーブした場合10と入力してください。

### 備考

- **厳選中に他のウィンドウに切り替えないでください！**
- 途中で停止した場合もレポートは保存されます。
- スキルの組み合わせはシリーズスキルかグループスキルのどちらか一方のみの設定でも問題ありません。
- 所持している素材分で抽選できる回数以上を指定した場合は、所持している素材分抽選しきった段階で終了します。
- 「当たりが出たら停止」をチェックしておけば、設定したスキルの組み合わせが出たらそこで停止します。スキルを実際に付与するかどうかの確認画面で終了します。
- 「終了後セーブせずタイトルに戻る」のチェックを外すとタイトルに戻りません。
- 武器種によっては状態異常属性と無属性のテーブルが同じ場合があるかもしれません。

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
            options_section,
            ft.Divider(height=20, color="transparent"),
            skills_card,
            ft.Divider(height=30, color="transparent"),
            ft.Row(
                [open_folder_button, run_button, route_button],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            ft.Divider(height=30, color="transparent"),
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

    page.padding = 0

    # --- Routes View ---
    def routes_view():
        # 現在の設定を取得
        targets = []
        for series_skill, group_skill in skill_sets:
            if series_skill.value or group_skill.value:
                s_val = series_skill.value if series_skill.value else ""
                g_val = group_skill.value if group_skill.value else ""
                targets.append([s_val, g_val])

        # 確定済み回数
        min_count = (
            int(confirmed_count_input.value)
            if confirmed_count_input.value and confirmed_count_input.value.isdigit()
            else 0
        )

        # 検索実行
        matches = table_manager.find_target_combinations(
            targets, min_count, MATCH_THRESHOLD
        )

        # 説明欄
        markdown_text = f"""
### 説明

あなたが設定したスキルの組み合わせが、厳選表の何回目に出現するかを調べた結果です。**何回目にどの武器でスキル再付与を行えばよいか**がわかります。

- 確定済み回数 (現在は{min_count}回) より後の回数のみが表示されます。
- 「付与したいスキルの組み合わせ」はあなたが設定したスキルの組み合わせです。
"""
        routes_description_container = ft.Container(
            content=ft.Markdown(
                markdown_text,
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
                on_tap_link=lambda e: page.launch_url(e.data),
            ),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_700),
            border_radius=10,
            margin=ft.margin.only(bottom=20),
        )

        # 結果リスト構築
        list_items = [routes_description_container]
        if not matches:
            list_items.append(
                ft.Container(
                    content=ft.Text(
                        "条件に一致する厳選ルートは見つかりませんでした。",
                        color=ft.Colors.GREY_500,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                )
            )
        else:
            for m in matches:
                count = m["count"]
                w_e = m["weapon_element"]
                combo = m["matched_combo"]
                detected = m.get("raw_skills", "")
                is_exact_match = m.get("is_exact_match", True)

                # コンボ表示用
                combo_str = " + ".join([c for c in combo if c])

                # タイトル行の要素を作成
                title_row_controls = [
                    ft.Text(
                        f"{count}回目",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.AMBER,
                    ),
                ]

                # カードコンテンツ
                card_controls = [
                    ft.Row(
                        [
                            ft.Row(
                                title_row_controls,
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    w_e,
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.ON_PRIMARY_CONTAINER,
                                ),
                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                border_radius=5,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=10, color="transparent"),
                    ft.Text(
                        f"付与したいスキルの組み合わせ: {combo_str}",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"ゲーム画面のOCR結果: {detected}",
                        size=12,
                        color=ft.Colors.GREY_500,
                    ),
                ]

                if not is_exact_match:
                    card_controls.append(
                        ft.Text(
                            "OCR結果が微妙に誤っているようです。念のため、「ゲーム画面のOCR結果」を確認して他のスキルの可能性がないか確認してください。",
                            size=11,
                            color=ft.Colors.RED_400,
                            weight=ft.FontWeight.BOLD,
                        )
                    )

                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column(card_controls),
                        padding=15,
                    ),
                    margin=ft.margin.only(bottom=10),
                )
                list_items.append(card)

        return ft.View(
            "/routes",
            [
                ft.AppBar(
                    title=ft.Text("厳選ルート"),
                    center_title=True,
                    bgcolor="surfaceVariant",
                    leading=ft.IconButton(
                        ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/")
                    ),
                ),
                ft.Container(
                    content=ft.Container(
                        content=ft.ListView(
                            controls=list_items,
                            expand=True,
                            padding=20,
                        ),
                        width=600,
                        padding=20,
                        alignment=ft.alignment.top_center,
                    ),
                    expand=True,
                    alignment=ft.alignment.top_center,
                ),
            ],
            padding=0,
        )

    # --- Routing ---
    def route_change(route):
        page.views.clear()

        # Main View
        page.views.append(
            ft.View(
                "/",
                [
                    ft.AppBar(
                        title=ft.Text("巨戟アーティア武器スキル厳選自動化ツール"),
                        center_title=True,
                        bgcolor="surfaceVariant",
                        actions=[
                            ft.Container(
                                content=reload_table_button,
                                margin=ft.margin.only(right=10),
                            )
                        ],
                    ),
                    ft.Container(
                        content=main_container,
                        expand=True,
                        alignment=ft.alignment.top_center,
                    ),
                ],
                padding=0,
            )
        )

        if page.route == "/routes":
            page.views.append(routes_view())

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)
