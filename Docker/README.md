# Docker 操作指南

## 基础配置

```bash
# 安装 Docker
# macOS
brew install --cask docker

# Linux
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io

# 验证安装
docker --version

# 启动 Docker 服务
sudo systemctl start docker

# 设置开机自启
sudo systemctl enable docker
```

## 核心概念

1. **镜像（Image）**
   - 只读模板，包含运行应用所需的所有内容
   - 示例：`ubuntu:20.04`, `nginx:latest`

2. **容器（Container）**
   - 镜像的运行实例
   - 轻量级、可移植、隔离的环境

3. **仓库（Registry）**
   - 存储和分发镜像的地方
   - 默认使用 Docker Hub

## 工作流程

### 1. 获取镜像

```bash
# 从 Docker Hub 拉取镜像
docker pull ubuntu:20.04

# 查看本地镜像
docker images
```

### 2. 运行容器

```bash
# 运行交互式容器
docker run -it ubuntu:20.04 /bin/bash

# 运行后台容器
docker run -d --name my-nginx nginx

# 查看运行中的容器
docker ps

# 查看所有容器
docker ps -a
```

### 3. 管理容器

```bash
# 启动/停止容器
docker start <container_id>
docker stop <container_id>

# 删除容器
docker rm <container_id>

# 查看容器日志
docker logs <container_id>

# 进入运行中的容器
docker exec -it <container_id> /bin/bash
```

### 4. 构建自定义镜像

1. 创建 Dockerfile
```Dockerfile
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y nginx
COPY index.html /var/www/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

2. 构建镜像
```bash
docker build -t my-nginx .
```

3. 运行自定义镜像
```bash
docker run -d -p 8080:80 --name my-nginx my-nginx
```

### 5. 推送镜像到仓库

```bash
# 登录 Docker Hub
docker login

# 标记镜像
docker tag my-nginx username/my-nginx:v1

# 推送镜像
docker push username/my-nginx:v1
```

## 高级操作

### 1. 数据持久化

```bash
# 创建数据卷
docker volume create my-volume

# 使用数据卷
docker run -d -v my-volume:/app/data my-app

# 查看数据卷
docker volume ls
```

### 2. 网络配置

```bash
# 创建自定义网络
docker network create my-network

# 使用自定义网络
docker run -d --name my-app --network my-network my-app

# 查看网络信息
docker network inspect my-network
```

### 3. Docker Compose

1. 创建 docker-compose.yml
```yaml
version: '3'
services:
  web:
    image: nginx
    ports:
      - "8080:80"
  db:
    image: mysql
    environment:
      MYSQL_ROOT_PASSWORD: example
```

2. 启动服务
```bash
docker-compose up -d
```

3. 停止服务
```bash
docker-compose down
```

## 最佳实践

1. **镜像优化**
   - 使用多阶段构建
   - 最小化镜像层数
   - 清理不必要的文件

2. **容器管理**
   - 使用资源限制
   - 配置健康检查
   - 实现日志轮转

3. **安全建议**
   - 使用非 root 用户运行容器
   - 定期更新基础镜像
   - 扫描镜像漏洞

4. **CI/CD 集成**
   - 在 CI 中构建和测试镜像
   - 使用镜像标签管理版本
   - 自动化部署流程

## 实际示例：Nginx 网站部署

### 1. 准备本地目录结构

```bash
# 创建项目目录
mkdir -p ~/my-nginx-project/{html,logs}

# 创建示例网页
echo "<h1>Hello Docker!</h1>" > ~/my-nginx-project/html/index.html
```

### 2. 运行 Nginx 容器

```bash
docker run -d \
  --name my-nginx \
  -p 8080:80 \
  -v ~/my-nginx-project/html:/usr/share/nginx/html \
  -v ~/my-nginx-project/logs:/var/log/nginx \
  nginx:latest
```

参数说明：
- `-d`：后台运行容器（detached mode）
- `--name my-nginx`：为容器指定名称（便于管理）
- `-p 8080:80`：端口映射（主机端口:容器端口）
  - 主机端口 8080 映射到容器的 80 端口
  - 可通过 http://localhost:8080 访问
- `-v`：目录挂载（主机目录:容器目录）
  - `~/my-nginx-project/html:/usr/share/nginx/html`：将主机 html 目录挂载到容器网站根目录
  - `~/my-nginx-project/logs:/var/log/nginx`：将主机 logs 目录挂载到容器日志目录
- `nginx:latest`：使用的镜像名称及标签

### 3. 验证部署

1. 在浏览器访问：http://localhost:8080
2. 查看日志文件：
```bash
tail -f ~/my-nginx-project/logs/access.log
```

### 4. 修改网站内容

```bash
# 编辑本地文件
vim ~/my-nginx-project/html/index.html

# 刷新浏览器查看变化
```

### 5. 停止和清理

```bash
# 停止容器
docker stop my-nginx

# 删除容器
docker rm my-nginx

# 保留本地数据以便下次使用
```

## 常用命令速查表

| 命令 | 描述 |
|------|------|
| `docker ps` | 查看运行中的容器 |
| `docker images` | 查看本地镜像 |
| `docker logs` | 查看容器日志 |
| `docker exec` | 在容器中执行命令 |
| `docker build` | 构建镜像 |
| `docker-compose up` | 启动 Compose 服务 |
| `docker volume ls` | 查看数据卷 |
| `docker network ls` | 查看网络 |

## 常见问题处理

1. **容器无法启动**
   ```bash
   docker logs <container_id>
   docker inspect <container_id>
   ```

2. **清理未使用的资源**
   ```bash
   docker system prune
   docker volume prune
   docker network prune
   ```

3. **查看容器资源使用情况**
   ```bash
   docker stats
   ```

4. **备份和恢复容器**
   ```bash
   # 备份
   docker commit <container_id> backup-image
   docker save -o backup.tar backup-image

   # 恢复
   docker load -i backup.tar
   docker run -d backup-image
   ```

## 总结

通过遵循这些最佳实践和使用这些命令，您可以更高效地使用 Docker 进行应用容器化，实现快速部署和可扩展的架构。
