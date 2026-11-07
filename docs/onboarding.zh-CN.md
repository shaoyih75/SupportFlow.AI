# SupportFlow.AI 新人上手指南（Mac）

这份指南带你从一台什么都没装的 Mac 开始，一步步把项目跑起来。每一步都写了**要输入什么**、**成功时会看到什么**、**失败了怎么办**。第一次大约需要 30–40 分钟，大部分时间在等下载。

跑完之后你会有：

- 浏览器里打开 http://localhost:3000 能用的网站
- 一个跑在 Docker 里的 PostgreSQL 数据库，里面有演示数据
- 能通过的 24 个测试
- 3 个演示账号（OWNER / MEMBER / VIEWER），能体验登录和权限控制

---

## 开始之前：先搞懂 5 件事

### 1. 终端是什么、怎么打开

终端（Terminal）就是输入命令的窗口。打开方式（任选一种）：

- 按 `⌘ + 空格`，输入 `Terminal`，回车。
- 或者在 VS Code 里：菜单 **Terminal → New Terminal**。**推荐用这个**，后面要开 3 个终端，VS Code 下方面板右上角的 `+` 可以一直新增，左边列表能切换。

终端里最后一行一般以 `%` 或 `❯` 结尾，这叫**提示符**，意思是"我在等你输入命令"。

### 2. 命令怎么输入

- 本文里灰色框中的每一行就是一条命令。**一次复制一行**，粘贴到终端，按回车。
- 等它运行完、**重新出现提示符**，再输入下一条。
- 行尾 `#` 后面的文字是说明，复制进去也没关系，终端会忽略它。

### 3. "当前目录"很重要

很多命令只能在特定目录里运行，放错地方就会报错。三个命令帮你确认位置：

| 命令 | 作用 |
|---|---|
| `pwd` | 显示你现在在哪个目录 |
| `ls` | 列出当前目录里有什么 |
| `cd 目录名` | 进入某个目录；`cd ..` 回到上一层 |

本文提到的两个位置：

- **项目根目录**：`SupportFlow.AI/` 本身，里面能看到 `docker-compose.yml`、`backend`、`frontend`。
- **backend 目录**：`SupportFlow.AI/backend/`，里面能看到 `alembic.ini`、`app`、`requirements.txt`。

不确定的时候，先运行 `pwd` 和 `ls` 看一眼。

### 4. 有的命令会"一直占着"终端

启动后端（`uvicorn ...`）和前端（`npm run dev`）的命令，运行后**不会回到提示符**，而是一直在打印日志。这是**正常的**，说明服务正在运行。

- **不要关掉这个终端窗口**，关掉服务就停了。
- 想停止它：在那个终端里按 `Ctrl + C`。
- 要输入别的命令，就**换一个终端**。所以我们需要 3 个终端：

| 终端 | 用途 | 所在目录 |
|---|---|---|
| 终端 1 | 运行 Docker 和数据库相关命令 | 项目根目录 |
| 终端 2 | 运行后端（会被 uvicorn 占住） | `backend/` |
| 终端 3 | 运行前端（会被 npm run dev 占住） | `frontend/` |

### 5. 出错了怎么办

1. 先看报错的**最后几行**，真正的原因通常在那里。
2. 到本文最后的「常见问题」里搜一下关键词。
3. 还是不行：把**整段报错**（不是截一小部分）连同你刚输入的命令，一起发给老师。

---

## 整体流程

```text
第 1 步  安装工具（只做一次）
第 2 步  下载代码
第 3 步  终端 1：启动数据库和 S3（Docker）
第 4 步  终端 2：后端 —— 装依赖 → 建表 → 写演示数据 → 启动
第 5 步  终端 3：前端 —— 装依赖 → 启动
第 6 步  浏览器里验证 + 跑测试
第 7 步  （可选）用 TablePlus 看数据库里的表
```

---

## 第 1 步：安装工具（只做一次）

打开**一个**终端，逐个检查。**能显示版本号就说明已经装好了**，跳过安装即可。

### 1.1 Homebrew（Mac 上装软件的工具）

```bash
brew --version
```

- 看到 `Homebrew 4.x.x` 之类：已安装。
- 看到 `command not found: brew`：打开 https://brew.sh ，复制首页那条安装命令到终端运行。装完后，**按它最后打印的提示**再运行两行命令（把 brew 加到 PATH），然后关掉终端重开。

⚠️ 安装过程中出现 `Password:` 时，输入你的 **Mac 开机密码**，然后按回车。**输入时屏幕上什么都不会显示**（没有星号），这是正常的，照常输完按回车就行。

### 1.2 Git、Python、Node.js

```bash
git --version
python3 --version
node -v
```

| 工具 | 需要的版本 | 没有或版本太低就运行 |
|---|---|---|
| Git | 任意 | `xcode-select --install`（会弹窗，点"安装"） |
| Python | `Python 3.11` 或更高 | `brew install python` |
| Node.js | `v20.9` 或更高 | `brew install node` |

### 1.3 Docker Desktop

```bash
brew install --cask docker-desktop
```

装完后：

1. 打开"应用程序"里的 **Docker**。
2. 第一次打开会让你同意条款；登录 Docker 账号那一步可以点 **Skip** 跳过。
3. 等屏幕顶部菜单栏出现**鲸鱼图标**，并且停止跳动。
4. **关掉当前终端，重新开一个**，然后验证：

```bash
docker run --rm hello-world
```

✅ 成功：输出里有一行 `Hello from Docker!`

❌ 看到 `Cannot connect to the Docker daemon`：Docker 应用还没打开或还没启动完，等鲸鱼图标停下来再试。

📌 **以后每次用这个项目之前，都要先打开 Docker 应用。**

### 1.4 TablePlus（可选，用来像 Excel 一样看数据库）

```bash
brew install --cask tableplus
```

---

## 第 2 步：下载代码

还是在这个终端里：

```bash
mkdir -p ~/Documents/projects
cd ~/Documents/projects
git clone https://github.com/shaoyih75/SupportFlow.AI.git
cd SupportFlow.AI
```

✅ 成功：显示 `Cloning into 'SupportFlow.AI'...`，最后没有 `fatal:` 报错。

检查一下位置：

```bash
pwd
ls
```

✅ `pwd` 显示 `.../Documents/projects/SupportFlow.AI`，`ls` 能看到 `README.md  backend  docker  docker-compose.yml  docs  frontend`。

这个终端以后就是**终端 1**。

---

## 第 3 步：启动数据库和 S3（终端 1，项目根目录）

确认 Docker 应用已经打开，然后：

```bash
docker compose up -d --wait
```

这条命令会启动两个容器：

- `db`：PostgreSQL 数据库，存 ticket、用户、文档信息等数据。
- `s3`：本地的 S3 文件存储，存上传的文件本身。

第一次会下载两个镜像（合计约 1GB），需要等几分钟。

✅ 成功时最后几行类似：

```text
✔ Container supportflowai-db-1   Healthy
✔ Container supportflowai-s3-1   Healthy
```

再确认一次：

```bash
docker compose ps
```

✅ `db` 和 `s3` 两行的 `STATUS` 都显示 `Up ... (healthy)`。

❌ 看到 `no configuration file provided`：你不在项目根目录，先 `cd ~/Documents/projects/SupportFlow.AI`。

---

## 第 4 步：后端（终端 2，backend 目录）

**新开一个终端**（VS Code 里点终端面板的 `+`），这就是**终端 2**。

### 4.1 进入 backend 目录

```bash
cd ~/Documents/projects/SupportFlow.AI/backend
```

### 4.2 创建并激活 Python 虚拟环境

虚拟环境 = 这个项目专用的 Python 环境，装的包不会影响电脑上的其他项目。

```bash
python3 -m venv .venv
source .venv/bin/activate
```

✅ 成功：提示符前面出现 `(.venv)`。

📌 **每次新开一个终端要运行后端命令时，都要先 `source .venv/bin/activate`**。没有 `(.venv)` 时运行 `alembic`、`uvicorn`、`pytest`，会报 `command not found`。

### 4.3 安装后端依赖

```bash
pip install -r requirements.txt
```

✅ 成功：最后一行是 `Successfully installed ...`。中间出现的 `[notice] A new release of pip is available` 可以忽略。

### 4.4 创建配置文件

```bash
cp .env.example .env
```

这条命令没有任何输出，是正常的。`.env` 里写着数据库和 S3 的地址，内容和 Docker 里的容器是对应的，不需要修改。

### 4.5 建表

```bash
alembic upgrade head
```

✅ 成功：最后两行是

```text
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial core schema
INFO  [alembic.runtime.migration] Running upgrade 0001 -> 0002, auth password hash and viewer role
INFO  [alembic.runtime.migration] Running upgrade 0002 -> 0003, documents for s3 uploads
```

确认一下：

```bash
alembic current
```

✅ 显示 `0003 (head)`。

⚠️ 这里只能用 `alembic upgrade head`。**不要**运行 `alembic revision --autogenerate`：那条命令是"写一个新的 migration 文件"，只有修改了 `models.py` 之后才需要用。

### 4.6 写入演示数据

```bash
python -m app.seed
```

✅ 第一次显示：

```text
Seeded: user alice@example.com, user bob@example.com, user carol@example.com, workspace Acme Support, ...
Demo logins: alice@ / bob@ / carol@example.com, password 'password123'
```

以后再运行会显示 `Demo data already present; nothing to do.`，不会重复写入。

这一步创建了 3 个演示账号，**密码都是 `password123`**（仅限本地开发）：

| 账号 | 角色 |
|---|---|
| `alice@example.com` | Acme Support 的 OWNER（全部权限） |
| `bob@example.com` | Acme Support 的 MEMBER（能建、能改，不能删）；自己私人 workspace 的 OWNER |
| `carol@example.com` | Acme Support 的 VIEWER（只能看） |

### 4.7 启动后端

```bash
uvicorn app.main:app --reload --port 8000
```

✅ 成功时会看到：

```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

然后终端就被占住了，**这是正常的**，不要关掉它。

用浏览器打开 http://localhost:8000/docs ，能看到 API 文档页面就说明后端好了。

---

## 第 5 步：前端（终端 3，frontend 目录）

**再新开一个终端**，这是**终端 3**。

```bash
cd ~/Documents/projects/SupportFlow.AI/frontend
npm install
```

✅ 成功：最后显示 `added ... packages`，没有红色的 `ERR!`。

```bash
npm run dev
```

✅ 成功时会看到：

```text
▲ Next.js 16.x
- Local:   http://localhost:3000
✓ Ready
```

这个终端也会被占住，同样不要关。

---

## 第 6 步：验证一切正常

### 6.1 在浏览器里试用

打开 http://localhost:3000 ，会跳到**登录页**。

1. 点下面的演示账号 **alice@example.com**（会自动填好邮箱和密码），再点 **Log in**。
2. 进入 "My workspaces"，点 **Acme Support**，左侧能看到 "Your role: OWNER"。
3. 点左侧 **Tickets**：能看到 5 个 ticket。
4. 在顶部表单输入标题（至少 3 个字），选优先级，点 **Create ticket**：新的 ticket 出现在列表最上面。
5. 只输入 2 个字再提交：输入框下面出现红色的校验错误（这是后端返回的 422）。
6. 点进一个 ticket，用 **Status** 下拉框改状态；OWNER 还能看到 **Delete ticket**。
7. 左上角切换到 **New Team**：显示 "No tickets yet"。

### 6.1.1 体验权限控制

1. 左下角点 **Log out**，再用 **carol@example.com** 登录（VIEWER）。
2. 进入 Acme Support → Tickets：能看到 ticket，但**没有创建表单**，显示 "read-only access"；点进 ticket 也**没有状态下拉框和删除按钮**。
3. 用 bob@example.com 登录（MEMBER）：能创建、能改状态，但**没有删除按钮**。
4. 把浏览器地址栏改成 `http://localhost:3000/workspaces/33333333-3333-3333-3333-333333333333`，用 Alice 或 Carol 访问：显示 "You don't have access to this workspace"（后端返回的 403）。

按钮被隐藏只是为了体验好；就算有人绕过前端直接调用 API，后端也会返回 403。

### 6.1.2 上传文档到 S3

1. 用 alice 登录，进入 Acme Support，点左侧 **Documents**。
2. 点 **Choose File**，选项目里的 `backend/scripts/handbook.txt`，再点 **Upload**。
3. 进度会依次显示：
    - `1/3 Asking the API for an upload link`：后端检查权限，在数据库里写一条 `PENDING` 记录。
    - `2/3 Uploading to S3 xx%`：文件直接传到 S3，**不经过我们的后端**。
    - `3/3 Server is verifying the file in S3`：后端去 S3 核对文件，确认无误后改成 `UPLOADED`。
4. 列表里出现 `handbook.txt`，状态是绿色的 **UPLOADED**。点 **Download** 能下载回同一个文件。
5. 选一张图片或 `.exe` 文件：页面直接提示 "Only PDF, TXT and Markdown"，不会上传。
6. 用 carol（VIEWER）登录：能看到文档列表，但没有上传区域。

在**终端 1**（项目根目录）确认文件和记录都在：

```bash
docker compose exec s3 awslocal s3 ls --recursive s3://supportflow-documents/
docker compose exec db psql -U supportflow -c "SELECT filename, storage_key, size_bytes, status FROM documents;"
```

✅ S3 里有一个 `workspaces/1111.../documents/<一串id>.txt` 的文件；数据库里有一行 `handbook.txt ... UPLOADED`。两边的 key 一样。

也可以不用浏览器，用脚本走一遍三步上传（在激活了 `.venv` 的 backend 目录里，后端要在运行）：

```bash
python scripts/upload_demo.py
```

⚠️ 本地 S3 把文件存在**内存**里：重启 Docker 或运行 `docker compose down` 之后，文件会消失，但数据库里的记录还在，这时点 Download 会失败。重新上传一次即可。真正的 AWS S3 不会丢文件。

### 6.2 证明数据真的存进了数据库（本课核心）

1. 回到**终端 2**，按 `Ctrl + C` 停掉后端。
2. 重新启动：

```bash
uvicorn app.main:app --reload --port 8000
```

3. 回到浏览器刷新页面：**刚才创建的 ticket 还在**。

如果数据存在内存里，重启后就会丢失；存在 PostgreSQL 里就不会。

### 6.3 跑测试

需要一个激活了 `.venv` 的终端，而终端 2 正被 uvicorn 占着，所以**再开一个终端**：

```bash
cd ~/Documents/projects/SupportFlow.AI/backend
source .venv/bin/activate
pytest -q
```

✅ 成功：最后一行是 `47 passed`。

测试用的是另一个数据库 `supportflow_test` 和另一个 S3 bucket `supportflow-documents-test`，不会影响你在网页上看到的数据。

---

## 第 7 步（可选）：用 TablePlus 看数据库里的表

1. 打开 **TablePlus**，点 **Create a new connection...**。
2. 选 **PostgreSQL**，点 **Create**。
3. 按下表填写：

| 字段 | 填写 |
|---|---|
| Name | `SupportFlow local`（随便起） |
| Host | `localhost` |
| Port | `5432` |
| User | `supportflow` |
| Password | `supportflow` |
| Database | `supportflow` |

4. 点 **Test**：输入框变绿说明连上了。再点 **Connect**。
5. 左侧双击 `tickets`，就能看到所有 ticket。在网页上新建一个 ticket 后，回到这里按 `⌘ + R` 刷新，新的一行就出现了。

⚠️ TablePlus 可以直接修改数据。练习时尽量只看不改。

不想装 TablePlus 的话，也可以在**终端 1**（项目根目录）用命令行看：

```bash
docker compose exec db psql -U supportflow -c "SELECT subject, status FROM tickets;"
```

---

## 用完之后：怎么关、第二天怎么再打开

### 关掉

- 终端 2、终端 3：各按一次 `Ctrl + C`。
- 数据库和 S3 可以不管它们，让它们在后台跑着；想关就在终端 1 运行 `docker compose stop`。
- 退出 Docker 应用、关机都**不会丢数据库里的数据**；但本地 S3 里上传的文件会丢，需要重新上传。

### 第二天再打开

**不需要**再装依赖、建表、写演示数据。先打开 Docker 应用，然后：

终端 1（项目根目录）：

```bash
cd ~/Documents/projects/SupportFlow.AI
docker compose up -d --wait
```

终端 2（backend）：

```bash
cd ~/Documents/projects/SupportFlow.AI/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

终端 3（frontend）：

```bash
cd ~/Documents/projects/SupportFlow.AI/frontend
npm run dev
```

### 拉取了新代码之后（`git pull`）

代码可能新增了依赖或 migration，多运行这几条：

```bash
# backend 目录，激活 .venv 之后
pip install -r requirements.txt
alembic upgrade head

# frontend 目录
npm install
```

### 想把数据库清空重来

终端 1（项目根目录）：

```bash
docker compose down -v
docker compose up -d --wait
```

然后回到第 4 步，重新做 4.5（`alembic upgrade head`）和 4.6（`python -m app.seed`）。⚠️ `down -v` 会**删除所有数据**。

---

## 常见问题

| 你看到的报错 | 原因 | 怎么解决 |
|---|---|---|
| `command not found: brew` | Homebrew 没装，或者装完没按提示加 PATH | 回到 1.1 |
| `command not found: docker` | Docker Desktop 没装好，或者装完没重开终端 | 打开 Docker 应用，关掉终端重开 |
| `Cannot connect to the Docker daemon` | Docker 应用没在运行 | 打开 Docker，等鲸鱼图标停止跳动 |
| `no configuration file provided` | 运行 `docker compose` 时不在项目根目录 | `cd ~/Documents/projects/SupportFlow.AI` |
| `command not found: alembic` / `uvicorn` / `pytest` | 没激活虚拟环境（提示符前没有 `(.venv)`） | 在 backend 目录运行 `source .venv/bin/activate` |
| `No 'script_location' key found` | 运行 alembic 时不在 backend 目录 | `cd ~/Documents/projects/SupportFlow.AI/backend` |
| `Connection refused ... port 5432` | 数据库没启动 | 终端 1 运行 `docker compose up -d --wait` |
| 上传时显示 "Cannot reach file storage" | S3 容器没启动 | 终端 1 运行 `docker compose up -d --wait` |
| 上传显示 "Only PDF, TXT and Markdown" | 文件类型不支持 | 换成 `.pdf`、`.txt` 或 `.md` 文件 |
| 上传显示 "Files must be 10 MB or smaller" | 文件超过 10MB | 换一个小一点的文件 |
| 重启 Docker 后 Download 失败 | 本地 S3 的文件存在内存里，重启就没了 | 重新上传 |
| `Target database is not up to date` | 运行了 `alembic revision` | 改成运行 `alembic upgrade head` |
| `Address already in use` / `address already in use` | 8000 或 3000 端口被别的程序占了 | 关掉那个程序；或者后端用 `--port 8001`，前端用 `BACKEND_URL=http://localhost:8001 npm run dev` 启动 |
| 网页左下角显示 "API offline" | 后端没在运行 | 去终端 2 启动 uvicorn |
| 登录时显示 "Invalid email or password" | 密码不对，或者没运行 seed（演示账号还没有密码） | 密码是 `password123`；在 backend 目录运行 `python -m app.seed` |
| 用着用着突然跳回登录页 | 登录 token 过期了（60 分钟），后端返回 401 | 重新登录即可，这是正常的 |
| 显示 "You don't have access to this workspace" | 当前账号不是这个 workspace 的成员（403） | 换一个有权限的账号，或回到 "My workspaces" |
| 网页显示 "Cannot reach the API server" | 同上 | 同上 |
| `npm ERR!` | Node 版本太低，或者网络问题 | `node -v` 确认版本 ≥ 20.9，然后重新 `npm install` |
| 输入密码时屏幕没反应 | 正常现象，终端不显示密码 | 照常输完按回车 |

---

## 最后的检查清单

全部打勾，就说明环境搭好了：

- [ ] `docker compose ps` 里 `db` 和 `s3` 都显示 `(healthy)`
- [ ] `alembic current` 显示 `0003 (head)`
- [ ] http://localhost:8000/docs 能打开
- [ ] 用 alice@example.com / password123 登录后，Acme Support 里能看到 5 个 ticket
- [ ] 用 carol@example.com 登录，看不到创建表单和编辑按钮
- [ ] 新建 ticket → 重启后端 → 刷新页面，ticket 还在
- [ ] Documents 页面上传 `handbook.txt`，状态变成 `UPLOADED`，能下载
- [ ] `pytest -q` 显示 `47 passed`

更多原理说明（为什么要分层、约束和索引、Transaction、Alembic、Docker 数据存在哪）见项目根目录的 [README.md](../README.md)。
