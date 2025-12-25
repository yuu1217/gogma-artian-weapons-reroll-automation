import pygetwindow as gw


def list_windows():
    titles = gw.getAllTitles()
    print("--- Open Windows ---")
    for t in titles:
        if t.strip():
            print(f"[{t}]")
    print("--------------------")


if __name__ == "__main__":
    list_windows()
