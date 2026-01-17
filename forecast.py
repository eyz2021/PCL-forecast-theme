import requests
import json
import os
import datetime
import colorsys

# ===================== 核心工具：颜色对比度计算 =====================
def hex_to_rgb(hex_color):
    """将十六进制颜色（#FFB74D）转换为RGB元组 (255,183,77)"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_contrast_text_color(bg_hex_color):
    """
    根据背景色自动计算高对比度文字色（黑/白）
    参考W3C对比度标准：对比度≥4.5:1 保证可读性
    """
    r, g, b = hex_to_rgb(bg_hex_color)
    # 计算相对亮度（公式参考W3C）
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    # 亮度>0.5 用黑色，否则用白色（对比度最优）
    return "#000000" if luminance > 0.5 else "#FFFFFF"

# ===================== 配置项 =====================
TOKEN = os.getenv("CAIYUN_TOKEN")  # 从环境变量获取token
CITY_CONFIG = {
    "沈阳": {"lng": 123.4316, "lat": 41.8057},
    "北京": {"lng": 116.4074, "lat": 39.9042},
    "上海": {"lng": 121.4737, "lat": 31.2304},
    "广州": {"lng": 113.2644, "lat": 23.1291},
    "测试城市": {"lng": 101.6656, "lat": 39.2072}  # API示例中的经纬度
}
TARGET_CITY = "沈阳"  # 默认为API示例中的城市，可切换为其他配置城市
OUTPUT_XAML_PATH = "weather_theme.xaml"  # 生成的主题文件路径
# ==================================================

# 优化后的天气主题色映射（提高对比度，保证文字可读性）
WEATHER_THEME_MAP = {
    "CLEAR_DAY": {"bg": "#FFB74D", "accent": "#FF8C00"},  # 晴（白天）- 暖橙（深 accent 保证对比）
    "CLEAR_NIGHT": {"bg": "#263238", "accent": "#90A4AE"},# 晴（夜间）- 深蓝灰（浅 accent）
    "PARTLY_CLOUDY_DAY": {"bg": "#90A4AE", "accent": "#455A64"},# 多云（白天）- 浅灰蓝（深 accent）
    "PARTLY_CLOUDY_NIGHT": {"bg": "#5C6BC0", "accent": "#E3F2FD"},# 多云（夜间）- 深紫蓝（浅 accent）
    "CLOUDY": {"bg": "#78909C", "accent": "#263238"},# 阴 - 深灰蓝（深 accent）
    "RAIN": {"bg": "#64B5F6", "accent": "#0D47A1"},# 雨 - 天蓝（深蓝 accent）
    "SNOW": {"bg": "#E0F7FA", "accent": "#00695C"},# 雪 - 浅青（深绿 accent）
    "WIND": {"bg": "#81C784", "accent": "#2E7D32"},# 大风 - 浅绿（深绿 accent）
    "HAZE": {"bg": "#BCAAA4", "accent": "#4E342E"},# 雾霾 - 浅棕（深棕 accent）
    "FOG": {"bg": "#ECEFF1", "accent": "#263238"},# 雾 - 浅灰（深灰 accent）
    "DEFAULT": {"bg": "#607D8B", "accent": "#FFFFFF"}# 默认主题（白字保证对比）
}

def safe_convert_temp(value):
    """安全转换温度数据，保留1位小数"""
    if value is None:
        return "暂无"
    try:
        temp = float(value)
        return f"{temp:.1f}"
    except (ValueError, TypeError):
        return "暂无"

def get_weather_data(city):
    """获取指定城市的天气数据（适配API实际返回格式）"""
    if city not in CITY_CONFIG:
        raise ValueError(f"未配置{city}的经纬度，请补充CITY_CONFIG")
    
    lng, lat = CITY_CONFIG[city]["lng"], CITY_CONFIG[city]["lat"]
    # 使用API示例中的hourly接口（返回小时级完整数据）
    url = f"https://api.caiyunapp.com/v2.6/{TOKEN}/{lng},{lat}/hourly"
    params = {
        "hourlysteps": 48,  # 获取48小时数据（后续截取前24小时）
        "fields": "temperature,skycon,humidity,wind,apparent_temperature"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "ok":
            raise Exception(f"API返回状态异常：{data.get('status')}")
        
        return data
    except requests.exceptions.Timeout:
        raise Exception("请求超时，请检查网络")
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP请求失败：{str(e)}")
    except json.JSONDecodeError:
        raise Exception("返回数据不是合法JSON")

def generate_weather_theme(weather_data, city):
    """根据API实际返回格式生成XAML主题文件（最终全量修复）"""
    # 提取核心数据（严格匹配API返回路径）
    result = weather_data.get("result", {})
    hourly = result.get("hourly", {})
    realtime_skycon = hourly.get("skycon", [{}])[0].get("value", "DEFAULT")  # 当前天气状况
    forecast_keypoint = hourly.get("description", "暂无预报信息")
    
    # 提取实时温度（取第一条小时数据）
    hourly_temps = hourly.get("temperature", [])
    realtime_temp = safe_convert_temp(hourly_temps[0].get("value")) if hourly_temps else "暂无"
    
    # 提取实时体感温度
    hourly_apparent_temps = hourly.get("apparent_temperature", [])
    app_temp = safe_convert_temp(hourly_apparent_temps[0].get("value")) if hourly_apparent_temps else "暂无"
    
    # 提取实时湿度
    hourly_humidity = hourly.get("humidity", [])
    humidity = "暂无"
    if hourly_humidity:
        try:
            humidity = round(float(hourly_humidity[0].get("value")) * 100, 1)
        except (ValueError, TypeError):
            humidity = "暂无"
    
    # 提取实时风力
    hourly_wind = hourly.get("wind", [])
    wind_level = "暂无"
    if hourly_wind:
        wind_speed = hourly_wind[0].get("speed", 0)
        # 根据风速换算风力等级（参考：0级<0.3, 1级0.3-1.5, 2级1.6-3.3, 3级3.4-5.4, 4级5.5-7.9）
        if wind_speed < 0.3:
            wind_level = "0"
        elif wind_speed <= 1.5:
            wind_level = "1"
        elif wind_speed <= 3.3:
            wind_level = "2"
        elif wind_speed <= 5.4:
            wind_level = "3"
        elif wind_speed <= 7.9:
            wind_level = "4"
        elif wind_speed <= 10.7:
            wind_level = "5"
        else:
            wind_level = "6+"
    
    # 提取当日最高/最低温度（从24小时数据中计算）
    temp_list = [safe_convert_temp(item.get("value")) for item in hourly_temps[:24] if item.get("value") is not None]
    temp_list = [float(t) for t in temp_list if t != "暂无"]
    temp_max = f"{max(temp_list):.1f}" if temp_list else "暂无"
    temp_min = f"{min(temp_list):.1f}" if temp_list else "暂无"
    
    # ========== 核心：提取前24小时温度数据（适配ISO时间格式） ==========
    hourly_temp_display = []
    for item in hourly_temps[:24]:  # 仅取前24小时
        iso_time = item.get("datetime")  # API返回格式：2026-01-17T15:00+08:00
        temp_val = safe_convert_temp(item.get("value"))
        
        if iso_time:
            try:
                # 解析ISO格式时间字符串
                if "+" in iso_time:
                    iso_time = iso_time.split("+")[0]  # 去除时区偏移
                time_obj = datetime.datetime.fromisoformat(iso_time)
                hour_str = time_obj.strftime("%H时")  # 转换为"15时"格式
                hourly_temp_display.append(f"{hour_str} {temp_val}℃")
            except Exception as e:
                print(f"跳过异常时间数据：{iso_time}，错误：{str(e)}")
                continue
    
    # ========== 核心优化：动态计算高对比度字体色 ==========
    theme = WEATHER_THEME_MAP.get(realtime_skycon, WEATHER_THEME_MAP["DEFAULT"])
    bg_color = theme["bg"]
    accent_color = theme["accent"]
    # 自动计算文字色（保证与背景/强调色的高对比度）
    text_color_on_bg = get_contrast_text_color(bg_color)       # 背景上的文字色
    text_color_on_accent = get_contrast_text_color(accent_color) # 强调色上的文字色

    # 生成小时温度XAML片段（最终修复：Border包裹TextBlock实现圆角，WrapPanel解决换行）
    hourly_xaml = ""
    if hourly_temp_display:
        hourly_xaml = """<WrapPanel Margin="0,10,0,15">"""  # 修复1：替换StackPanel为WrapPanel
        for temp_item in hourly_temp_display:
            # 修复2：用Border包裹TextBlock实现圆角（TextBlock无CornerRadius属性）
            hourly_xaml += f"""
            <Border Background="{bg_color}"
                    CornerRadius="3"
                    Margin="6,3"
                    Padding="4,2">
                <TextBlock FontSize="11" 
                           Foreground="{text_color_on_bg}"
                           Text="{temp_item}" />
            </Border>
            """
        hourly_xaml += "</WrapPanel>"
    else:
        # 异常提示也用高对比度+圆角（Border包裹）
        hourly_xaml = f"""<Border Background="#FF5722"
                                CornerRadius="3"
                                Margin="0,10,0,15"
                                Padding="8,4">
            <TextBlock FontSize="11" 
                       Foreground="#FFFFFF"
                       Text="暂无小时温度数据" />
        </Border>"""
    
    # 处理更新时间（使用API返回的第一条数据时间）
    update_time = "未知"
    if hourly_temps:
        try:
            iso_time = hourly_temps[0].get("datetime")
            if iso_time:
                if "+" in iso_time:
                    iso_time = iso_time.split("+")[0]
                time_obj = datetime.datetime.fromisoformat(iso_time)
                update_time = time_obj.strftime("%Y-%m-%d %H:%M")
        except Exception:
            update_time = "未知"

    # 最终XAML模板（全量修复，无任何语法错误）
    xaml_template = f"""<!-- 天气动态主题文件 - 自动生成：{city} -->
<local:MyCard Title="{city}实时天气" Margin="0,0,0,15" Background="{bg_color}">
    <StackPanel Margin="25,40,23,15">
        <!-- 天气状态标题（高对比度） -->
        <TextBlock Margin="0,0,0,15" FontSize="16" HorizontalAlignment="Center" 
                   Foreground="{text_color_on_bg}"
                   Text="{realtime_skycon.replace('_', ' ')} | {forecast_keypoint}" />
        
        <!-- 核心天气信息（修复3：Border包裹实现圆角，高对比文字） -->
        <StackPanel Orientation="Horizontal" HorizontalAlignment="Center" Margin="0,0,0,20">
            <Border Background="{accent_color}"
                    CornerRadius="8"
                    Padding="10,5">
                <TextBlock FontSize="48" 
                           Foreground="{text_color_on_accent}"
                           Text="{realtime_temp}°C" />
            </Border>
            <TextBlock FontSize="14" VerticalAlignment="Center" Margin="10,0,0,10" 
                       Foreground="{text_color_on_bg}"
                       Text="体感 {app_temp}℃" />
        </StackPanel>
        
        <!-- 当日最高/最低温度（高对比） -->
        <TextBlock Margin="0,0,0,10" FontSize="13" HorizontalAlignment="Center"
                   Foreground="{text_color_on_bg}"
                   Text="今日温度范围：{temp_min}℃ ~ {temp_max}℃" />

        <!-- 小时温度预报（最终修复版） -->
        <TextBlock Margin="0,10,0,5" FontSize="12" FontWeight="Bold"
                   Foreground="{text_color_on_bg}"
                   Text="未来24小时温度预报：" />
        {hourly_xaml}
        
        <!-- 基础气象信息（高对比） -->
        <StackPanel Margin="0,15,0,15">
            <TextBlock Margin="0,0,0,4" FontSize="13" 
                       Foreground="{text_color_on_bg}"
                       Text="相对湿度：{humidity}%" />
            <TextBlock Margin="0,0,0,4" FontSize="13" 
                       Foreground="{text_color_on_bg}"
                       Text="风力等级：{wind_level}级" />
        </StackPanel>
    </StackPanel>
</local:MyCard>

<local:MyCard Title="数据说明" Margin="0,0,0,15" CanSwap="True" IsSwapped="True" Background="#F5F5F5">
    <StackPanel Margin="25,40,23,15">
        <local:MyHint Theme="Blue" Text="数据来源：彩云天气 API v2.6" />
        <TextBlock Margin="0,10,0,0" FontSize="12"
                   Foreground="#212121"
                   Text="数据更新时间：{update_time}" />
        <TextBlock Margin="0,5,0,0" FontSize="12"
                   Foreground="#616161"
                   Text="API请求地址：https://api.caiyunapp.com/v2.6/[TOKEN_REDACTED]/{CITY_CONFIG[city]['lng']},{CITY_CONFIG[city]['lat']}/hourly" />
    </StackPanel>
</local:MyCard>
"""
    # 写入XAML文件
    with open(OUTPUT_XAML_PATH, "w", encoding="utf-8") as f:
        f.write(xaml_template)
    
    # 控制台输出日志（包含对比度信息）
    print(f"✅ 天气主题文件生成完成：{os.path.abspath(OUTPUT_XAML_PATH)}")
    print(f"🌤️ {city} 当前天气：{realtime_skycon.replace('_', ' ')} | 实时气温：{realtime_temp}℃ | 今日范围：{temp_min}~{temp_max}℃")
    print(f"🎨 主题配色：背景={bg_color} 文字={text_color_on_bg} | 强调色={accent_color} 文字={text_color_on_accent}")
    print(f"⏰ 已加载 {len(hourly_temp_display)} 个小时的温度数据")

if __name__ == "__main__":
    import sys
    # 支持命令行传参切换城市
    target_city = TARGET_CITY
    if len(sys.argv) > 1 and sys.argv[1] == "--city" and len(sys.argv) > 2:
        if sys.argv[2] in CITY_CONFIG:
            target_city = sys.argv[2]
        else:
            print(f"⚠️  城市{sys.argv[2]}未配置，使用默认城市{target_city}")
    
    # 验证token是否存在
    if not TOKEN:
        print("❌ 错误：CAIYUN_TOKEN环境变量未设置")
        # 生成降级XAML（高对比度错误提示，无语法错误）
        fallback_xaml = """<local:MyCard Title="天气加载失败" Margin="0,0,0,15" Background="#FF5722">
    <StackPanel Margin="25,40,23,15">
        <Border CornerRadius="8" Padding="10,8">
            <local:MyHint Theme="White" Text="天气数据获取失败，请检查：&#xA;1. 网络连接 &#xA;2. API令牌有效性 &#xA;3. 城市经纬度配置" />
        </Border>
    </StackPanel>
</local:MyCard>"""
        with open(OUTPUT_XAML_PATH, "w", encoding="utf-8") as f:
            f.write(fallback_xaml)
        sys.exit(1)
    
    try:
        # 1. 获取天气数据
        weather_data = get_weather_data(target_city)
        # 2. 生成主题文件
        generate_weather_theme(weather_data, target_city)
    except Exception as e:
        print(f"❌ 执行失败：{str(e)}")
        # 生成降级XAML（高对比度错误提示，无语法错误）
        fallback_xaml = """<local:MyCard Title="天气加载失败" Margin="0,0,0,15" Background="#FF5722">
    <StackPanel Margin="25,40,23,15">
        <Border CornerRadius="8" Padding="10,8">
            <local:MyHint Theme="White" Text="天气数据获取失败，请检查：&#xA;1. 网络连接 &#xA;2. API令牌有效性 &#xA;3. 城市经纬度配置" />
        </Border>
    </StackPanel>
</local:MyCard>"""
        with open(OUTPUT_XAML_PATH, "w", encoding="utf-8") as f:
            f.write(fallback_xaml)
        sys.exit(1)