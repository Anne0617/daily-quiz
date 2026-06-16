"""Desktop automation sender for WeCom (企业微信)"""
import time
import pygetwindow as gw
import pyautogui
import pyperclip

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


def _find_wecom():
    """Find the WeCom main window handle."""
    try:
        import win32gui
        def enum_cb(hwnd, lst):
            if win32gui.IsWindowVisible(hwnd):
                t = win32gui.GetWindowText(hwnd)
                if "\u4f01\u4e1a\u5fae\u4fe1" in t or "WeCom" in t:
                    lst.append(hwnd)
            return True
        hwnds = []
        win32gui.EnumWindows(enum_cb, hwnds)
        if hwnds:
            for w in gw.getAllWindows():
                if hasattr(w, "_hWnd") and w._hWnd in hwnds:
                    return w
    except Exception:
        pass
    for w in gw.getAllWindows():
        if w.title and ("\u4f01\u4e1a\u5fae\u4fe1" in w.title or "WeCom" in w.title):
            return w
    return None


def send_to_wecom_group(group_name: str, message: str) -> bool:
    """Send message to WeCom group via desktop UI automation."""
    pyperclip.copy(message)
    time.sleep(0.3)
    
    wecom = _find_wecom()
    if not wecom:
        print("ERROR: WeCom not running")
        return False
    
    print(f"Found WeCom, activating...")
    # Restore if minimized
    try:
        import win32gui, win32con
        hwnd = wecom._hWnd
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        wecom.activate()
    time.sleep(1.5)
    
    # Ctrl+F -> search bar
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.write(group_name, interval=0.03)
    time.sleep(1.0)
    
    # Enter to open first result
    pyautogui.press("enter")
    time.sleep(1.5)
    
    # Click message input area
    l, t = wecom.left, wecom.top
    w, h = wecom.width, wecom.height
    pyautogui.click(l + int(w*0.5), t + int(h*0.88), clicks=1, button="left")
    time.sleep(0.5)
    
    # Paste and send
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.8)
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
