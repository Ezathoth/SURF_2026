# SURF_2026

在 GitHub 仓库中创建文件夹和上传文件的两种方法：**Git 命令行** 和 **GitHub 网页界面**。

---

## 方法一：使用 Git 命令行（本地操作）

1. **克隆仓库到本地**（若尚未克隆）：
   ```bash
   git clone https://github.com/你的用户名/仓库名.git
   cd 仓库名
   ```

2. **创建文件夹**（例如 `docs`）：
   ```bash
   mkdir docs
   ```

3. **在文件夹中创建文件**（例如 `docs/README.md`）：
   ```bash
   touch docs/README.md
   # 或直接写入内容
   echo "# 项目文档" > docs/README.md
   ```

4. **将文件夹和文件添加到暂存区**：
   ```bash
   git add docs/
   ```

5. **提交变更**（附带描述信息）：
   ```bash
   git commit -m "添加 docs 文件夹及 README 文件"
   ```

6. **推送到远程仓库**（主分支通常为 `main` 或 `master`）：
   ```bash
   git push origin main
   ```

> 💡 **提示**：如果远程分支不是 `main`，请替换为实际分支名（如 `master`）。

---

## 方法二：使用 GitHub 网页界面（在线操作）

1. 进入你的仓库主页，点击 **Add file** 下拉按钮，选择 **Create new file**。

2. 在文件名输入框中，**直接输入包含文件夹路径的文件名**，例如 `docs/README.md`。  
   GitHub 会自动根据斜杠 `/` 创建对应的文件夹。

3. 在文件编辑区编写内容，完成后滚动到页面底部：
   - 填写提交信息（如“创建 docs 文件夹并添加 README”）
   - 选择 **Commit directly to the main branch**（或创建新分支并提交 PR）
   - 点击 **Commit new file**。

4. **上传多个文件或整个文件夹**：  
   点击 **Add file** → **Upload files**，然后将文件或文件夹直接拖拽到上传区域，最后提交变更。

---

## 验证结果

无论使用哪种方法，操作完成后刷新仓库页面，即可在文件列表中看到新建的 `docs` 文件夹及其中的文件。
