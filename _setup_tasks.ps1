# 学习强企 · Windows 计划任务注册脚本
# ==========================================
# 使用方法：以管理员身份运行 PowerShell，执行：
#   powershell -ExecutionPolicy Bypass .\_setup_tasks.ps1
# ==========================================

$workspace = "D:\HuaweiMoveData\Users\Anna\Documents\学习强企-企业微信智能机器人打卡"
$python = "python"

Write-Host "正在注册计划任务..." -ForegroundColor Cyan

# -------- 任务 1：每日 09:00 推送知识点+问卷 --------
$action1 = New-ScheduledTaskAction -Execute $python -Argument "scheduler.py push" -WorkingDirectory $workspace
$trigger1 = New-ScheduledTaskTrigger -Daily -At "09:00"
$principal1 = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "学习强企-每日推送" -Action $action1 -Trigger $trigger1 -Principal $principal1 -Force
Write-Host "  [OK] 每日 09:00 推送知识点+问卷" -ForegroundColor Green

# -------- 任务 2：每日 18:00 推送答题进度 --------
$action2 = New-ScheduledTaskAction -Execute $python -Argument "scheduler.py stats" -WorkingDirectory $workspace
$trigger2 = New-ScheduledTaskTrigger -Daily -At "18:00"
$principal2 = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "学习强企-每日统计" -Action $action2 -Trigger $trigger2 -Principal $principal2 -Force
Write-Host "  [OK] 每日 18:00 推送答题进度" -ForegroundColor Green

# -------- 任务 3：每周五 16:00 催办 --------
$action3 = New-ScheduledTaskAction -Execute $python -Argument "scheduler.py reminder" -WorkingDirectory $workspace
$trigger3 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At "16:00"
$principal3 = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "学习强企-每周催办" -Action $action3 -Trigger $trigger3 -Principal $principal3 -Force
Write-Host "  [OK] 每周五 16:00 催办未答题人员" -ForegroundColor Green

Write-Host ""
Write-Host "全部注册完成！" -ForegroundColor Cyan
Write-Host "可通过「任务计划程序」查看和管理这三个任务。" -ForegroundColor Cyan
