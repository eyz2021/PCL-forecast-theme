# PCL Themes 天气主题生成器

## 功能介绍

这是一个自动生成天气主题文件的工具，使用彩云天气API获取天气数据，并根据天气状况动态生成XAML主题文件。

## GitHub Actions 配置

### 1. 配置 GitHub Secrets

在GitHub仓库的`Settings > Secrets and variables > Actions`中添加以下Secret：

- `CAIYUN_TOKEN`：彩云天气API令牌

### 2. GitHub Actions 工作流

项目已配置GitHub Actions工作流，功能如下：

- 每4小时自动执行一次（通过cron表达式`0 */4 * * *`控制）
- 代码推送到main分支时也会执行
- 自动安装依赖、生成主题文件并提交到仓库
- 不会泄露敏感信息（token从Secrets获取）

### 3. 工作流文件位置

`.github/workflows/generate-theme.yml`

## 本地运行

### 1. 安装依赖

```bash
pip install requests
```

### 2. 设置环境变量

```bash
export CAIYUN_TOKEN="你的彩云天气API令牌"  # Linux/Mac
set CAIYUN_TOKEN="你的彩云天气API令牌"  # Windows
```

### 3. 运行程序

```bash
python forecast.py
```

### 4. 命令行参数

- `--city`：指定城市（必须在CITY_CONFIG中配置）

示例：
```bash
python forecast.py --city 北京
```

## 配置说明

### 城市配置

在`forecast.py`中可以配置多个城市：

```python
CITY_CONFIG = {
    "沈阳": {"lng": 123.4316, "lat": 41.8057},
    "北京": {"lng": 116.4074, "lat": 39.9042},
    # 可添加更多城市
}
```

### 默认城市

```python
TARGET_CITY = "沈阳"  # 默认城市
```

### 输出文件路径

```python
OUTPUT_XAML_PATH = "weather_theme.xaml"  # 生成的主题文件路径
```

## 天气主题映射

程序根据天气状况使用不同的主题配色：

- 晴（白天）：暖橙色
- 晴（夜间）：深蓝灰色
- 多云（白天）：浅灰蓝色
- 多云（夜间）：深紫蓝色
- 阴：深灰蓝色
- 雨：天蓝色
- 雪：浅青色
- 大风：浅绿色
- 雾霾：浅棕色
- 雾：浅灰色

每个主题都经过对比度优化，确保文字清晰可读。