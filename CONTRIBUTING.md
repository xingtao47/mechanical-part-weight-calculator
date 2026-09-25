# 参与项目

感谢你关注机械零件重量计算器。你可以通过报告程序错误、提出功能建议或提交代码来帮助改进项目。

## 报告程序错误

请在 GitHub Issues 中选择“程序错误反馈”，并尽量提供：

- 软件版本和 Windows 版本。
- 出现问题前的操作步骤。
- 实际结果和预期结果。
- 不包含隐私信息的截图。

## 提出功能建议

请在 GitHub Issues 中选择“新功能建议”，说明功能的使用场景、期望行为，以及它能解决什么问题。

## 提交代码

1. Fork 本仓库并创建单独的功能分支。
2. 保持修改范围清晰，不提交 `build`、`dist`、`.spec` 和个人导出文件。
3. 在项目目录运行全部测试：

   ```powershell
   python -m unittest -v
   ```

4. 确认测试全部通过后再提交 Pull Request。
5. 在 Pull Request 中说明修改目的、主要变化和测试结果。

## 本地运行

运行图形界面：

```powershell
python weight_calculator_gui.py
```

运行命令行版本：

```powershell
python weight_calculator.py
```

本项目使用 Python 标准库运行；只有打包 Windows EXE 时才需要额外安装 PyInstaller。
