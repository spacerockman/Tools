
HI，老铁们！

老金来给大家伙儿讲讲怎么在Windows系统上配置Cursor的MCP服务器。

这玩意儿配好了，写代码效率蹭蹭往上涨！

跟着老金的步骤来，保证你也能配置成功！

第一部分：啥是MCP服务器？
MCP（Model Context Protocol）是让AI助手能调用外部工具和数据的协议。

简单说，就是让你的Cursor AI助手能做更多事情：

直接访问你电脑上的文件
联网查找信息
分析复杂问题
浏览器自动化操作
获取热点新闻
老金配置好这些后，编程效率直接起飞！不用再手动查资料，AI都能帮你搞定。

第二部分：前期准备
1. 安装Node.js和npm首先，你得有Node.js环境，没有的话按下面步骤安装：
按Win+R，输入cmd，打开命令提示符
输入node --version和npm --version
如果显示版本号（类似v18.x.x和9.x.x），说明安装成功了
打开浏览器，访问 Node.js官网
下载最新的LTS（长期支持）版本，别下那个Current版本
运行下载的安装包，一路Next，确保勾选"Add to PATH"选项
安装完成后，验证安装成功：
2. 准备必要的目录Cursor的MCP配置文件需要放在一个特定位置：
按Win+R，输入cmd，打开命令提示符
输入以下命令创建必要的目录：
mkdir %USERPROFILE%\.cursor
第三部分：安装MCP服务器包
老金要告诉你，我们需要提前安装几个服务器包，省得后面报错：

1. 在命令提示符中输入以下命令（一条一条执行）：
npm install -g @kazuph/mcp-fetch
npm install -g @modelcontextprotocol/server-sequential-thinking
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @wopal/mcp-server-hotnews
npm install -g @executeautomation/playwright-mcp-server
安装过程中可能会出现一些警告，别管它，只要没有报红色的错误就行。

第四部分：创建MCP配置文件
这是最关键的一步！老金发现Windows系统下配置MCP服务器，最大的坑就是命令格式问题！

1. 在文本编辑器中（可以用记事本或VS Code）创建一个新文件
2. 复制以下内容（完整配置，一个字都别改）：
{
  "mcpServers": {
    "fetch": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "@kazuph/mcp-fetch",
        "--config",
        "{}"
      ]
    },
    "thinking": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "@modelcontextprotocol/server-sequential-thinking",
        "--config",
        "{}"
      ]
    },
    "files": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:/Users/admin/Downloads"
      ]
    },
    "hotnews": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "@wopal/mcp-server-hotnews"
      ]
    },
    "playwright": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "@executeautomation/playwright-mcp-server"
      ]
    }
  }
}
1. 注意：修改files服务器中的路径"C:/Users/admin/Downloads"，把"admin"改成你自己的Windows用户名。这个路径决定AI助手能访问哪个文件夹。
2. 将文件保存为mcp.json
3. 将文件移动到正确位置：
按Win+R，输入%USERPROFILE%\.cursor，回车
将刚刚创建的mcp.json文件复制到这个目录
第五部分：配置说明和注意事项
老金要强调几个重要点：

1. 路径格式：在配置文件中，所有路径都要用正斜杠/而不是反斜杠\
2. 命令格式：所有服务器都要用cmd作为command，第一个args参数要是/c，这是Windows特有的坑
3. 服务器说明：
fetch：让AI能联网查询信息
thinking：让AI能进行顺序思考，解决复杂问题
files：让AI能读取你电脑上的文件
hotnews：让AI能获取实时热点新闻
playwright：让AI能操作浏览器自动化任务
第六部分：测试配置是否成功
1. 完成上述步骤后，先关闭Cursor（如果已经打开）
2. 重新启动Cursor
3. 打开Cursor的设置（左下角齿轮图标）
4. 点击"MCP Servers"
5. 检查是否显示了我们配置的5个服务器，且没有红色错误提示
第七部分：实际使用示例
老金给你几个实用示例，测试一下配置是否成功：

1. 测试文件访问：在Cursor聊天中输入
   使用files工具列出我的Downloads文件夹中的文件
2. 测试热点新闻：在Cursor聊天中输入
   使用hotnews工具获取今天的热点新闻
3. 测试联网查询：在Cursor聊天中输入
使用fetch工具搜索最新的JavaScript框架信息
第八部分：常见问题排查
如果配置后还是不工作，老金给你几个排查方向：

1. "Failed to create client"错误：
检查npm包是否真的安装成功
确认配置文件中的命令格式是否正确
尝试以管理员身份运行Cursor
2. 找不到命令错误：
执行npm config get prefix查看npm全局安装路径
确保该路径已添加到系统PATH环境变量
3. 路径错误：
确保文件路径正确且使用正斜杠/
确保路径不包含特殊字符
4. 执行策略问题：
以管理员身份打开PowerShell
执行Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
结语
行了，按照老金的这套配置方法，你的Cursor AI助手肯定能变得更强大！

如果还有啥问题，随时找老金。

记住一句话：用AI就是为了提高效率，省下的时间可以多陪陪家人，或者研究更多新技术！

老金的经验之谈：千万别纠结那些不存在的服务器包。有些网上教程推荐的包根本就不存在，配了也没用，别浪费时间！

用老金给的这些，够用了！



往期推荐：

LLM(大语言模型相关)全套教程列表

WX机器人教程列表

AI绘画教程列表

AI编程教程列表

硅基流动 Siliconflow教程列表

谢谢你读我的文章。



如果觉得不错，随手点个赞、在看、转发三连吧

如果想第一时间收到推送，也可以给我个星标⭐～谢谢你看我的文章。

发布于 2025-04-22 20:21・北京
Cursor
Mcp
​赞同 15​
​12 条评论
​分享
​喜欢
​收藏
​申请转载
​
  