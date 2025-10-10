# 使用 Python 官方镜像作为基础
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置时区（重要！）
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖清单
COPY requirements.txt .

# 安装Python依赖（开发模式）
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 启动命令（同时运行定时任务和Flask）
CMD ["sh", "-c", "python stock_price_updater.py & python run.py"]

