# GitHub网络连接测试脚本
# 用于诊断GitHub访问问题

Write-Host "=== GitHub网络连接测试 ===" -ForegroundColor Cyan
Write-Host "测试时间: $(Get-Date)"
Write-Host ""

# 1. 测试基础网络连接
Write-Host "1. 基础网络连接测试..." -ForegroundColor Yellow
$pingResult = Test-Connection -ComputerName "github.com" -Count 2 -Quiet
if ($pingResult) {
    Write-Host "   ✅ Ping成功" -ForegroundColor Green
} else {
    Write-Host "   ❌ Ping失败" -ForegroundColor Red
}

# 2. 测试HTTPS端口
Write-Host "`n2. HTTPS端口(443)测试..." -ForegroundColor Yellow
try {
    $tcpTest = Test-NetConnection -ComputerName "github.com" -Port 443 -WarningAction SilentlyContinue
    if ($tcpTest.TcpTestSucceeded) {
        Write-Host "   ✅ TCP 443端口连接成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ TCP 443端口连接失败" -ForegroundColor Red
        Write-Host "      Ping RTT: $($tcpTest.PingReplyDetails.RTT)ms" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ TCP测试异常: $_" -ForegroundColor Red
}

# 3. 测试Git端口
Write-Host "`n3. Git端口(9418)测试..." -ForegroundColor Yellow
try {
    $gitTest = Test-NetConnection -ComputerName "github.com" -Port 9418 -WarningAction SilentlyContinue
    if ($gitTest.TcpTestSucceeded) {
        Write-Host "   ✅ Git端口连接成功" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Git端口连接失败" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Git端口测试异常" -ForegroundColor Red
}

# 4. 测试网页访问
Write-Host "`n4. GitHub网页访问测试..." -ForegroundColor Yellow
try {
    $webTest = Invoke-WebRequest -Uri "https://github.com" -TimeoutSec 10 -ErrorAction Stop
    if ($webTest.StatusCode -eq 200) {
        Write-Host "   ✅ GitHub网页访问成功" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ GitHub网页访问返回状态: $($webTest.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ GitHub网页访问失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Git命令测试
Write-Host "`n5. Git远程连接测试..." -ForegroundColor Yellow
cd "C:\Users\LX\WorkBuddy\20260409105630\moss"
$gitResult = git ls-remote https://github.com/luokaishi/moss 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Git远程连接成功" -ForegroundColor Green
} else {
    Write-Host "   ❌ Git远程连接失败" -ForegroundColor Red
    Write-Host "      错误信息: $gitResult" -ForegroundColor Gray
}

# 6. 代理配置检查
Write-Host "`n6. 网络代理配置检查..." -ForegroundColor Yellow
$env:HTTP_PROXY
$env:HTTPS_PROXY
if ($env:HTTP_PROXY -or $env:HTTPS_PROXY) {
    Write-Host "   ⚠️ 检测到代理配置" -ForegroundColor Yellow
    Write-Host "      HTTP_PROXY: $($env:HTTP_PROXY)"
    Write-Host "      HTTPS_PROXY: $($env:HTTPS_PROXY)"
} else {
    Write-Host "   ✅ 无代理配置" -ForegroundColor Green
}

# 7. Git配置检查
Write-Host "`n7. Git配置检查..." -ForegroundColor Yellow
$gitConfig = git config --list
$remoteUrl = git config --get remote.origin.url
Write-Host "   远程仓库URL: $remoteUrl"
if ($remoteUrl -like "*https://*") {
    Write-Host "   ⚠️ 使用HTTPS协议" -ForegroundColor Yellow
} elseif ($remoteUrl -like "*git@*") {
    Write-Host "   ✅ 使用SSH协议" -ForegroundColor Green
}

Write-Host "`n=== 解决方案建议 ===" -ForegroundColor Cyan

# 根据测试结果提供建议
if (-not $tcpTest.TcpTestSucceeded) {
    Write-Host "`n🔧 建议1: 检查防火墙设置" -ForegroundColor Yellow
    Write-Host "   1. 确保443端口未被防火墙阻止"
    Write-Host "   2. 检查企业网络策略"
    Write-Host "   3. 尝试临时关闭防火墙测试"
}

if ($env:HTTP_PROXY -or $env:HTTPS_PROXY) {
    Write-Host "`n🔧 建议2: 配置Git使用代理" -ForegroundColor Yellow
    Write-Host "   git config --global http.proxy $env:HTTP_PROXY"
    Write-Host "   git config --global https.proxy $env:HTTPS_PROXY"
}

if ($remoteUrl -like "*https://*" -and -not $tcpTest.TcpTestSucceeded) {
    Write-Host "`n🔧 建议3: 切换到SSH协议" -ForegroundColor Yellow
    Write-Host "   git remote set-url origin git@github.com:luokaishi/moss.git"
    Write-Host "   需要先配置SSH密钥"
}

Write-Host "`n🔧 建议4: 使用备用同步方法" -ForegroundColor Yellow
Write-Host "   1. 在其他网络环境同步"
Write-Host "   2. 下载ZIP文件手动合并"
Write-Host "   3. 使用VPN或代理服务"

Write-Host "`n=== 测试完成 ===" -ForegroundColor Cyan
Write-Host "请根据测试结果选择相应的解决方案。"