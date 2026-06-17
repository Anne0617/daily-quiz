"""Desktop automation sender for WeCom (企业微信)"""
import time
import pygetwindow as gw
import pyautogui
import pyperclip

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.3


def _find_wecom():
    """Find the WeCom main window handle."""
    try:
        import win32gui
        def enum_cb(hwnd, lst):
            t = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if "企业微信" in t or "WeCom" in t or cls == "WeWorkWindow":
                lst.append(hwnd)
            return True
        hwnds = []
        win32gui.EnumWindows(enum_cb, hwnds)
        if hwnds:
            for h in hwnds:
                try:
                    w = gw.Window(h)
                    if w:
                        return w
                except Exception:
                    continue
    except Exception:
        pass
    for w in gw.getAllWindows():
        if w.title and ("企业微信" in w.title or "WeCom" in w.title or "WeWork" in w.title):
            return w
    return None


def _bring_wecom_to_front(hwnd):
    """Bring WeCom window to foreground using multiple methods."""
    import win32gui, win32con, win32api, win32process

    rect = win32gui.GetWindowRect(hwnd)
    wx, wy, wr, wb = rect
    win_w = wr - wx
    win_h = wb - wy

    # Get work area
    mi = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0, 0)))
    work = mi['Work']
    work_left, work_top, work_right, work_bottom = work

    # 1. Move to visible position if off-screen
    if wx < -1000 or wy < -1000 or wx > work_right or wy > work_bottom:
        new_w = min(1200, work_right - work_left - 100)
        new_h = min(780, work_bottom - work_top - 100)
        new_x = work_left + (work_right - work_left - new_w) // 2
        new_y = work_top + (work_bottom - work_top - new_h) // 2
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP,
                              new_x, new_y, new_w, new_h,
                              win32con.SWP_SHOWWINDOW)
        time.sleep(0.5)

    # 2. Show window (restore from tray)
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
    time.sleep(0.5)

    # 3. Force foreground with AttachThreadInput trick
    try:
        # Get foreground window thread and our thread
        foreground = win32gui.GetForegroundWindow()
        if foreground != hwnd:
            foreground_tid = win32process.GetWindowThreadProcessId(foreground)[1]
            target_tid = win32process.GetWindowThreadProcessId(hwnd)[1]
            our_tid = win32api.GetCurrentThreadId()

            # Attach threads to allow SetForegroundWindow
            if foreground_tid != target_tid:
                win32process.AttachThreadInput(our_tid, target_tid, True)
                win32process.AttachThreadInput(target_tid, foreground_tid, True)

            win32gui.SetForegroundWindow(hwnd)

            # Detach threads
            win32process.AttachThreadInput(our_tid, target_tid, False)
            win32process.AttachThreadInput(target_tid, foreground_tid, False)
    except Exception:
        pass

    # 4. Fallback: SwitchToThisWindow (bypasses foreground lock)
    import ctypes
    try:
        ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
    except Exception:
        pass

    time.sleep(1.0)

    # Verify and retry if needed
    for retry in range(3):
        if win32gui.GetForegroundWindow() == hwnd:
            return True
        time.sleep(0.5)
        try:
            ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
        except Exception:
            pass

    return win32gui.GetForegroundWindow() == hwnd


def send_to_wecom_group(group_name: str, message: str) -> bool:
    """Send message to WeCom group via desktop UI automation."""
    pyperclip.copy(message)
    time.sleep(0.3)

    wecom = _find_wecom()
    if not wecom:
        print("ERROR: WeCom not running")
        return False

    print(f"Found WeCom, bringing to front...")
    ok = _bring_wecom_to_front(wecom._hWnd)
    fg = __import__('win32gui').GetWindowText(__import__('win32gui').GetForegroundWindow())
    print(f"Foreground is WeCom: {ok} (current: {fg})")
    time.sleep(1.5)

    # Ctrl+F -> search bar
    pyautogui.hotkey("ctrl", "f")
    time.sleep(1.0)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyautogui.write(group_name, interval=0.03)
    time.sleep(1.5)

    # Enter to open first result
    pyautogui.press("enter")
    time.sleep(2.5)

    # Get fresh window position
    try:
        import win32gui
        rect = win32gui.GetWindowRect(wecom._hWnd)
        l, t = rect[0], rect[1]
        w, h = rect[2] - rect[0], rect[3] - rect[1]
    except Exception:
        l, t = wecom.left, wecom.top
        w, h = wecom.width, wecom.height

    # Click message input area
    pyautogui.click(l + int(w*0.5), t + int(h*0.88), clicks=1, button="left")
    time.sleep(1.0)

    # Paste and send
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(1.0)
    pyautogui.press("enter")
    time.sleep(0.5)

    print("Message sent!")
    return True


if __name__ == "__main__":
    import sys
    g = sys.argv[1] if len(sys.argv) > 1 else ""
    m = sys.argv[2] if len(sys.argv) > 2 else "Test"
    if g:
        print(f"Testing send to: {g}")
        send_to_wecom_group(g, m)
    else:
        print("Usage: python desktop_sender.py <group_name> [message]")
