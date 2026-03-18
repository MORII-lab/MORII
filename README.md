# 微光对话

这是一个鼓励型静态网页，打开后可以像聊天一样输入生活故事，得到更温柔、更接近真人倾听风格的回应。

## 本地打开

- 直接双击 `index.html`
- 或双击 `start-site.bat`，然后访问 `http://localhost:3000/`

## 发布成公网网址

这个项目已经带了 GitHub Pages 自动部署配置。

你只需要：

1. 在 GitHub 新建一个仓库
2. 把当前目录推送到这个仓库
3. 在 GitHub 仓库里打开 `Settings -> Pages`
4. 确认来源使用 `GitHub Actions`
5. 等待 Actions 跑完

部署完成后，网址通常会是：

`https://你的用户名.github.io/你的仓库名/`

## 推送示例

如果你已经创建好了 GitHub 仓库，把下面的命令里的地址换成你的仓库地址再运行：

```bash
git add .
git commit -m "Add support chat website"
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin master
```
