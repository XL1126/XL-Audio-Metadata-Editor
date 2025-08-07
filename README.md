# XL音频元数据编辑工具

一个简单易用的音频元数据编辑工具，支持为MP3、FLAC、M4A、OGG等格式的音频文件添加或修改封面图片及元数据（标题、艺术家、专辑、年份）。

## 功能特性

- **格式支持**：MP3、FLAC、M4A、OGG
- **元数据编辑**：
  - 基础信息：标题、艺术家、专辑、年份
  - 封面图片：支持JPG/PNG格式
- **无损处理**：仅修改元数据，不影响音频质量
- **直观界面**：简洁易用的中文GUI操作界面

##  界面预览

![程序界面截图](https://github.com/XL1126/XL-Audio-Metadata-Editor/blob/main/build/XL%20audio%20metadata%20editing%20tool/image.png)


##  下载安装

### 直接使用
前往 [Releases页面](https://github.com/XL1126/XL-Audio-Metadata-Editor/releases) 下载最新版可执行程序

### 从源码运行
```bash
# 克隆仓库
git clone https://github.com/XL1126/XL-Audio-Metadata-Editor.git
cd XL-Audio-Metadata-Editor

# 安装依赖
pip install Pillow>=10.0.0 mutagen>=1.47.0

# 运行程序
python XL音频元数据编辑工具.py
```
也可以不用这么麻烦，直接下载就行

##  开发构建

### 依赖说明
- **tkinter**：图形用户界面（GUI）框架  
- **PIL (Pillow)**：图像处理（如封面嵌入）  
- **os**：文件系统路径操作  
- **tempfile**：临时文件管理  
- **shutil**：高级文件操作（移动/复制）  
- **base64**：二进制数据编码/解码  
- **mutagen**：音频元数据读写（核心依赖）  
- **threading**：多线程处理（避免界面卡顿）  
- **io**：内存文件流操作  

tkinter、os、tempfile、shutil、base64、threading 和 io 是 Python 内置库（标准库），通常不需要额外安装，只需在代码中执行下面命令安装两个依赖即可。  
```bash
pip install Pillow>=10.0.0 mutagen>=1.47.0
```

然后运行：

```bash
python XL音频元数据编辑工具.py
```

### 打包为EXE
```bash
pip install pyinstaller

# 使用spec文件打包
pyinstaller XL音频元数据编辑工具.spec

# 或直接打包
pyinstaller --onefile --windowed --icon=app.ico XL音频元数据编辑工具.py
```

##  使用指南

1. 下载并运行最新版本的exe文件
2. 点击"浏览..."选择需要编辑的音频文件
3. （可选）点击"浏览..."选择要设置的封面图片，或使用现有封面
4. 编辑元数据信息（标题、艺术家、专辑、年份）
5. 选择保存位置（默认在原文件目录下生成带封面的新文件）
6. 点击"开始嵌入"按钮完成编辑

##  作者信息
- **作者**：XL(小狸)

##  其他事项
如果该项目有更多人支持，作者会继续更新。比如英文版、更好的布局或更多的功能。
本人的技术有限制作，可能不是很好，还请理解。
项目中涉及到的文件都在这里了，大家可以随意下载
