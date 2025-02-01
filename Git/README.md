# Git 操作指南

## 基础配置

```bash
# 初始化仓库
git init

# 查看当前配置
git config -l

# 设置全局用户名和邮箱
git config --global user.name "YourName"
git config --global user.email "your.email@example.com"

# 启用颜色显示
git config --global color.ui true
```

## 工作流程

### 1. 创建功能分支

```bash
git checkout -b my-feature
```

### 2. 查看变更

```bash
git diff
```

### 3. 添加文件到暂存区

```bash
# 添加所有变更
git add .

# 添加指定文件
git add <changed_file>
```

### 4. 提交变更

```bash
git commit -m "描述性提交信息"
```

### 5. 推送分支

```bash
git push origin my-feature
```

### 6. 处理远程主分支更新

```bash
# 切换到主分支
git checkout master

# 拉取最新代码
git pull origin master

# 切换回功能分支
git checkout my-feature

# 变基操作
git rebase master

# 强制推送
git push -f origin my-feature
```

### 7. 创建 Pull Request

- 在代码托管平台创建 PR
- 等待代码审查和合并

### 8. 合并后清理

```bash
# 切换到主分支
git checkout master

# 删除本地功能分支
git branch -D my-feature

# 更新本地主分支
git pull origin master
```

## 高级操作

### 1. 撤销操作

```bash
# 撤销暂存区文件
git reset HEAD <file>

# 撤销工作区修改
git checkout -- <file>
```

### 2. 修改最后一次提交

```bash
git commit --amend
```

### 3. Cherry-pick

```bash
# 切换到目标分支
git checkout target-branch

# 选择特定提交
git cherry-pick commitId1 commitId2 ...
```

### 4. 查看文件历史

```bash
git log --pretty=oneline <filename>
```

## 最佳实践

1. **提交信息规范**
   - 使用英文描述
   - 遵循 Conventional Commits 规范
   - 示例：`feat: add user authentication`

2. **分支管理**
   - 功能分支命名：`feature/xxx`
   - 修复分支命名：`fix/xxx`
   - 发布分支命名：`release/xxx`

3. **代码审查**
   - 保持小规模提交
   - 每个提交只完成一个功能
   - 提供清晰的提交说明

4. **冲突解决**
   - 优先使用 rebase 而不是 merge
   - 及时解决冲突
   - 测试后再推送

5. **Git 钩子**
   - 使用 pre-commit 进行代码检查
   - 使用 commit-msg 验证提交信息格式
   - 使用 pre-push 进行自动化测试

## 保持 Git 提交历史清晰

保持 Git 提交历史的干净和清晰是团队协作和代码维护的重要实践。以下是一些建议和技巧：

### 1. **使用清晰且有意义的提交信息**
   - 提交信息应简洁明了，描述清楚做了什么改动。
   - 遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范，例如：
     ```
     feat: 添加用户登录功能
     fix: 修复登录页面样式问题
     docs: 更新 README 文档
     refactor: 重构用户认证逻辑
     ```
   - 避免使用模糊的提交信息，如 `update` 或 `fix bug`。

### 2. **保持提交的原子性**
   - 每个提交应该只完成一个逻辑上的改动。
   - 避免将多个不相关的改动放在一个提交中。
   - 如果发现提交了不相关的内容，可以使用 `git add -p` 或 `git commit --amend` 来拆分或修正提交。

### 3. **使用交互式 rebase 整理提交历史**
   - 在合并分支或推送代码前，使用 `git rebase -i` 整理提交历史。
   - 通过交互式 rebase，可以：
     - 合并多个小提交（squash）。
     - 修改提交信息（reword）。
     - 删除不必要的提交（drop）。
     - 调整提交顺序（reorder）。
   - 示例：
     ```bash
     git rebase -i HEAD~5  # 整理最近 5 个提交
     ```

### 4. **避免频繁的合并提交**
   - 使用 `rebase` 代替 `merge` 来整合分支，避免产生多余的合并提交。
   - 例如，在将特性分支合并到主分支时：
     ```bash
     git checkout feature-branch
     git rebase main
     git checkout main
     git merge feature-branch
     ```

### 5. **定期清理本地和远程分支**
   - 删除已经合并到主分支的特性分支：
     ```bash
     git branch -d feature-branch  # 删除本地分支
     git push origin --delete feature-branch  # 删除远程分支
     ```
   - 使用 `git fetch --prune` 清理本地仓库中已经不存在的远程分支引用。

### 6. **使用 `git stash` 暂存未完成的工作**
   - 如果当前工作未完成，但需要切换分支，可以使用 `git stash` 暂存改动：
     ```bash
     git stash
     git checkout other-branch
     # 完成其他任务后
     git checkout original-branch
     git stash pop
     ```

### 7. **避免直接推送到主分支**
   - 使用特性分支（feature branch）开发新功能或修复问题。
   - 通过 Pull Request（PR）或 Merge Request（MR）进行代码审查和合并。
   - 这样可以确保主分支的提交历史清晰且稳定。

### 8. **使用 `git log` 查看提交历史**
   - 使用 `git log` 查看提交历史，确保提交信息清晰、历史记录整洁。
   - 推荐使用以下命令查看更清晰的日志：
     ```bash
     git log --oneline --graph --decorate
     ```

### 9. **避免强制推送（`git push --force`）**
   - 强制推送会覆盖远程提交历史，可能导致团队协作问题。
   - 如果必须强制推送，推荐使用 `--force-with-lease`，它更安全：
     ```bash
     git push --force-with-lease
     ```

### 10. **使用 Git Hooks 自动化检查**
   - 使用 Git 钩子（hooks）在提交或推送时自动检查代码风格、测试等。
   - 例如，在 `.git/hooks/pre-commit` 中添加脚本，确保代码符合规范。

### 11. **定期同步主分支**
   - 如果主分支（如 `main` 或 `master`）有更新，定期将其同步到你的特性分支：
     ```bash
     git checkout feature-branch
     git rebase main
     ```

### 12. **使用工具辅助管理**
   - 使用 Git 图形化工具（如 `gitk`、`Sourcetree`、`GitKraken`）查看和管理提交历史。
   - 使用 `tig` 命令行工具查看更直观的提交历史。

### 示例工作流
1. 创建特性分支：
   ```bash
   git checkout -b feature-branch
   ```
2. 开发并提交代码：
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   ```
3. 同步主分支：
   ```bash
   git checkout main
   git pull origin main
   git checkout feature-branch
   git rebase main
   ```
4. 整理提交历史：
   ```bash
   git rebase -i HEAD~3
   ```
5. 推送代码并创建 PR：
   ```bash
   git push origin feature-branch
   ```

## 常用命令速查表

| 命令 | 描述 |
|------|------|
| `git status` | 查看当前状态 |
| `git log --oneline` | 查看简洁提交历史 |
| `git stash` | 暂存当前修改 |
| `git stash pop` | 恢复暂存修改 |
| `git rebase -i` | 交互式变基 |
| `git reflog` | 查看所有操作记录 |
| `git bisect` | 二分查找问题提交 |

## 常见问题处理

1. **误删分支恢复**
   ```bash
   git reflog
   git checkout -b <branch-name> <commit-hash>
   ```

2. **撤销已推送提交**
   ```bash
   git revert <commit-hash>
   git push origin <branch-name>
   ```

3. **清理历史记录**
   ```bash
   git filter-branch --tree-filter 'rm -f <file>' HEAD
   git push origin --force
   ```

## Git Stash 详细教程

### 基本用法
- **暂存当前修改**（包含已 `git add` 的更改）：
  ```bash
  git stash
  ```
  或添加描述信息：
  ```bash
  git stash save "描述信息"
  ```

- **查看所有暂存记录**：
  ```bash
  git stash list
  ```

- **恢复最近暂存的修改**（并删除记录）：
  ```bash
  git stash pop
  ```

- **恢复指定暂存记录**（不删除记录）：
  ```bash
  git stash apply stash@{n}  # n 为 git stash list 中的编号
  ```

- **删除指定暂存记录**：
  ```bash
  git stash drop stash@{n}
  ```

- **清空所有暂存记录**：
  ```bash
  git stash clear
  ```

### 进阶用法
- **暂存未跟踪的文件**（新建文件）：
  ```bash
  git stash -u
  ```

- **暂存指定文件**：
  ```bash
  git stash push path/to/file1 path/to/file2
  ```

- **从暂存记录创建新分支**：
  ```bash
  git stash branch new-branch-name stash@{n}
  ```

---

## Git Rebase 详细教程

### 合并提交
1. **启动交互式变基**（合并最近 3 个提交）：
   ```bash
   git rebase -i HEAD~3
   ```

2. **编辑提交操作**（在文本编辑器中）：
   ```text
   pick 1a2b3c4 提交1描述
   squash 5d6e7f8 提交2描述  # 合并到前一个提交
   squash 9g0h1i2 提交3描述
   ```
   - `pick`: 保留提交
   - `squash`/`s`: 合并到前一个提交
   - `reword`/`r`: 修改提交信息
   - `drop`/`d`: 删除提交

3. **编辑最终提交信息**（保存后自动完成合并）

### 分支变基
- **将当前分支变基到目标分支**：
  ```bash
  git checkout feature-branch
  git rebase main          # 将 feature-branch 的基准点移动到 main 最新提交
  ```

- **强制推送更新**（仅限私有分支）：
  ```bash
  git push --force-with-lease
  ```

### 解决冲突
1. 变基过程中出现冲突时：
   ```bash
   # 手动解决冲突文件后
   git add resolved-file.txt
   git rebase --continue   # 继续变基
   ```

2. **中止变基**：
   ```bash
   git rebase --abort
   ```

### 注意事项
- 使用前先备份分支：
  ```bash
  git branch backup-branch
  ```
- 已推送到远程的提交不要变基
- 使用 `--force-with-lease` 比 `--force` 更安全


## 总结

通过遵循这些最佳实践和使用这些命令，您可以更高效地使用 Git 进行版本控制，保持代码库的整洁和可维护性。
