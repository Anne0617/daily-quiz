from pathlib import Path
from config import settings
from models import import_users_from_list


def import_from_excel(filepath: str = None) -> list:
    if filepath is None:
        filepath = settings.user_list_file
    fp = Path(filepath)
    if not fp.exists():
        print(f"文件不存在: {fp}")
        return []
    try:
        import openpyxl
    except ImportError:
        print("请先安装 openpyxl: pip install openpyxl")
        return []
    wb = openpyxl.load_workbook(str(fp))
    ws = wb.active
    users = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row and row[0]:
            name = str(row[0]).strip()
            dept = str(row[1]).strip() if len(row) > 1 and row[1] else ""
            if name:
                users.append((name, dept))
    return users


def main():
    filepath = settings.user_list_file
    users = import_from_excel(filepath)
    if not users:
        print(f"未读取到用户数据，请确认 {filepath} 格式正确（第一列姓名，第二列部门）")
        return
    print(f"读取到 {len(users)} 条用户记录")
    for name, dept in users[:5]:
        print(f"  {name} - {dept}")
    if len(users) > 5:
        print(f"  ... 共 {len(users)} 条")
    import_users_from_list(users)
    print("导入完成！")


if __name__ == "__main__":
    main()
