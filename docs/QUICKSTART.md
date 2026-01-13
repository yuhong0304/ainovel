# 🚀 快速入门指南

5分钟内开始使用 Novel Agent 创作你的第一部小说！

---

## 📥 第一步：安装

### Windows 用户
直接双击 `install.bat`，等待安装完成即可。

### Mac/Linux 用户
```bash
chmod +x install.sh
./install.sh
```

---

## 🔑 第二步：配置 API Key

1. 打开项目根目录下的 `.env` 文件（如果没有，复制 `.env.example` 并重命名）
2. 填入你的 API Key：

```ini
GEMINI_API_KEY=你的Gemini API密钥
```

### 如何获取 Gemini API Key？

1. 访问 [Google AI Studio](https://aistudio.google.com/app/apikey)
2. 登录你的 Google 账号
3. 点击 "Create API Key"
4. 复制生成的密钥

---

## ▶️ 第三步：启动

### Windows
双击 `start.bat`，选择模式 `1`（Web界面）

### Mac/Linux
```bash
./start.sh
```

浏览器会自动打开 `http://localhost:5000`

---

## 📝 第四步：创建你的第一部小说

1. 在 Web 界面点击 **"新建项目"**
2. 输入项目名称（如：我的玄幻小说）
3. 在灵感框中输入你的创意：
   ```
   一个现代程序员穿越到修仙世界，
   利用编程思维理解功法，成为一代宗师的故事
   ```
4. 点击 **"生成元提示"** → AI 会分析你的灵感
5. 点击 **"生成总纲"** → AI 会生成完整的故事大纲
6. 继续生成卷纲、章纲、正文...

---

## 💡 提示

- **随时可以暂停**: 所有进度自动保存
- **可以修改任何内容**: AI 会从你的修改中学习
- **导出成品**: 完成后可以导出为 TXT/DOCX/EPUB

---

## ❓ 常见问题

### Q: 安装失败提示找不到 Python？
A: 请先安装 Python 3.9+，下载地址：https://python.org/downloads

### Q: 启动后浏览器打不开？
A: 手动访问 http://localhost:5000

### Q: API 调用报错？
A: 检查 `.env` 文件中的 API Key 是否正确

---

准备好了吗？开始创作吧！🎉
