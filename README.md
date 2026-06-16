# 星河十五五规划 · 企业微信每日打卡考试系统

## 概述
基于企业微信群机器人的每日考试系统，自动从 PDF 文档提炼知识点和考题，
每天上午 9:00 推送至经理群，成员点击链接完成自测，自动判分并生成周报。

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
set DEEPSEEK_API_KEY=your_deepseek_api_key
set WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
set BASE_URL=http://your-server:8080
```

### 3. 导入经理名单
将名单放入 user_list/managers.xlsx（第一列姓名，第二列部门），然后：
```bash
python user_importer.py
```

### 4. 生成题库
将 PDF 文档放入 data/pdfs/，然后：
```bash
python content_processor.py --auto-publish
```

### 5. 启动服务
```bash
python main.py
```

### 6. 设置定时任务
Windows Task Scheduler:
- 每日 9:00: python scheduler.py push
- 每周一 10:00: python scheduler.py week_report
