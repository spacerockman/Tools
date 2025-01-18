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

## 总结

通过遵循这些最佳实践和使用这些命令，您可以更高效地使用 Git 进行版本控制，保持代码库的整洁和可维护性。
