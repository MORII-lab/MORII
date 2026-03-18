# 微光对话

一个帮助人、鼓励人、愿意认真听生活故事的 AI 陪伴网页。

当前默认接的是 `Gemini`，适合先用免费额度把网站跑起来。

## 现在已经有的能力

- 更自然的对话式回复
- 前后端分离的 AI 接口
- 危机关键词检测与紧急支持提示
- 固定人格：`微光`
- 多轮对话记忆
- 聊天记录保存、恢复、删除与导出
- 默认支持 `Gemini`

## 本地运行

1. 复制环境变量模板：

```bash
copy .env.example .env
```

2. 在 `.env` 里填入：

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.5-flash-lite
PORT=3000
MORII_PERSONA_NAME=微光
MORII_PERSONA_TAGLINE=像一个沉静、真诚、不评判人的深夜来信朋友。
CRISIS_SUPPORT_TEXT=如果你有可能马上伤害自己、伤害别人，或已经无法保证安全，请立刻联系当地紧急服务，或者马上去最近的医院/急诊。也请尽快联系一个你信任的人，让对方现在陪着你。
```

3. 启动：

```bash
python server.py
```

4. 打开：

`http://localhost:3000/`

## 公网部署

GitHub Pages 只能托管静态页面，不适合安全保存 `GEMINI_API_KEY`。  
如果要让别人在线使用真 AI，对话后端需要部署到支持服务端环境变量的平台。

这个仓库已经补好了 Render 部署配置：

- [render.yaml](./render.yaml)
- [requirements.txt](./requirements.txt)

一键部署入口：

[Deploy to Render](https://render.com/deploy?repo=https://github.com/MORII-lab/MORII/tree/master)

部署后还需要在 Render 后台补一个环境变量：

- `GEMINI_API_KEY`

Render 会给你一个公网地址，格式通常像：

- `https://你的服务名.onrender.com`

## 项目文件

- `index.html`：前端页面和聊天逻辑
- `server.py`：后端接口、危机检测和 Gemini 调用
- `.env.example`：环境变量模板
- `render.yaml`：Render 部署配置
- `start-site.bat`：本地一键启动

## 说明

- 没有配置 `GEMINI_API_KEY` 时，网站仍可运行，但会回退到本地温柔模式，不会调用真 AI。
- 危机提示不是专业心理或医疗服务，遇到真实风险时仍应优先联系当地紧急支持系统。
