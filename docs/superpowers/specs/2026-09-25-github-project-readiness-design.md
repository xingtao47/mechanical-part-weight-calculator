# GitHub 项目发布完善设计

## 目标

将机械零件重量计算器仓库完善为一个普通用户容易了解、下载和反馈问题的公开项目，同时使用 GitHub Actions 自动验证代码质量。

本次工作只完善项目发布、说明和维护流程，不新增重量计算功能，也不改变 V2.0 的计算结果和操作方式。

## 当前状态

- V2.0 源代码和 `v2.0` 标签已经推送到 GitHub。
- Windows EXE 已在本机和其他 Windows 电脑上测试通过。
- 项目已有 README、CHANGELOG、27 项自动测试和手动打包脚本。
- 项目尚无开源许可证、软件截图、Issue 模板、贡献说明和 GitHub Actions。
- V2.0 ZIP 已在本地生成，但仍需作为 GitHub Release 附件上传。

## README 与下载入口

README 按普通用户优先的顺序重新组织：

1. 项目名称和一句话用途。
2. 自动测试状态徽章。
3. “下载最新版”链接，指向仓库的 Releases 最新版本页面。
4. V2.0 软件主界面真实截图。
5. 支持的系统和使用说明。
6. 主要功能、材料、零件类型和计算公式。
7. 常见问题。
8. 问题反馈入口。
9. 开发、测试和打包说明。
10. 许可证和版本记录。

README 明确说明：

- 打包后的 EXE 面向 64 位 Windows 10 和 Windows 11；未经实际测试的系统不作兼容性保证。
- 使用 EXE 不需要安装 Python。
- 软件离线运行，不上传或收集用户输入的数据。
- Windows 第一次运行未签名 EXE 时可能显示安全提醒。
- Python 源码可供开发者运行和检查。

## 软件截图

- 启动已通过测试的 V2.0 EXE，使用真实程序窗口制作截图。
- 截图保存到 `docs/images/v2.0-main-window.png`。
- 截图中使用示例零件数据，不包含个人路径、用户名或其他隐私信息。
- README 使用仓库相对路径展示截图，确保 GitHub 页面可以直接显示。

## 开源许可证

- 在仓库根目录新增 `LICENSE`。
- 使用 MIT License。
- 版权年份使用 2026，版权人使用 GitHub 用户名 `xingtao47`。
- README 增加许可证说明并链接到 `LICENSE`。

## 问题反馈与贡献

新增以下文件：

- `.github/ISSUE_TEMPLATE/bug_report.yml`：收集软件版本、Windows 版本、问题描述、复现步骤、预期结果和截图。
- `.github/ISSUE_TEMPLATE/feature_request.yml`：收集功能用途、期望行为和使用场景。
- `.github/ISSUE_TEMPLATE/config.yml`：关闭空白 Issue，并提供使用说明入口。
- `CONTRIBUTING.md`：说明如何提交问题、提出功能建议、运行测试和提交代码。

README 中提供直接进入 Issues 页面的反馈链接。暂不增加行为准则、论坛、赞助和复杂社区管理文件。

## GitHub Actions 自动测试

新增 `.github/workflows/tests.yml`，行为如下：

- 在推送到 `main` 和针对 `main` 的 Pull Request 时运行。
- 使用 GitHub 托管的 `windows-latest` 环境。
- 使用官方 `actions/checkout` 检出代码。
- 使用官方 `actions/setup-python` 安装 Python 3.12。
- 执行 `python -m unittest -v`。
- 工作流只读取代码和运行测试，不发布文件、不创建标签、不修改仓库内容。

README 增加指向该工作流的状态徽章。工作流成功时显示绿色，失败时显示红色。

## V2.0 Release

准备一份可直接复制到 GitHub 的 V2.0 Release 说明，包含：

- Windows 桌面图形界面。
- 支持的零件、材料和尺寸单位。
- 清单汇总与 CSV 导出。
- 下载和运行步骤。
- 面向 64 位 Windows 10/11 的系统说明。
- 文件为未进行商业代码签名的独立开发版本。

Release 使用现有 `v2.0` 标签，标题为“机械零件重量计算器 V2.0”，上传本地 `dist/机械零件重量计算器-V2.0.zip`，并设置为最新正式版本。

EXE 和 ZIP 继续由 `.gitignore` 排除，不提交到普通代码历史中。

## 验证

- 本地运行 `python -m unittest -v`，确认 27 项测试全部通过。
- 检查 README 内部文件链接和 GitHub 链接。
- 检查 Issue 模板 YAML 格式与必填字段。
- 检查 GitHub Actions YAML 语法、触发条件和命令。
- 确认软件截图能在 README 中显示且不包含隐私信息。
- 提交后推送 `main`，确认 GitHub Actions 首次运行通过。
- 创建或更新 V2.0 Release，确认 ZIP 可以下载。

## 不包含在本次工作中

- 不开发新的零件类型、材料或计算公式。
- 不自动构建或自动发布 EXE。
- 不购买或配置 Windows 代码签名证书。
- 不创建网站、账户系统、云同步或在线数据库。
- 不修改或提交无关的 `pelican-cycling.html`。
