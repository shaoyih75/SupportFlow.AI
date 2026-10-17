# 第 6 课作业：注册页 + 新建 Workspace

后端接口都已经写好了，这次作业主要写前端：让一个新人自己注册账号、建 Workspace、开始使用，不再依赖 alice / bob / carol 这三个演示账号。

## 开始前

```bash
git checkout main && git pull           # 拿到第 6 课的代码
git checkout -b homework/register       # 在自己的分支上做
cd backend && pytest -q                 # 先确认现在是 24 passed
```

先在 Swagger（http://localhost:8000/docs）里手动调一次 `POST /api/auth/register`，分别试试成功、邮箱重复、密码太短三种情况，看看各返回什么。

## 需要用到的后端接口

| 接口 | 请求体 | 成功 | 失败 |
| --- | --- | --- | --- |
| `POST /api/auth/register` | `name`（1–100 字）、`email`、`password`（8–72 位） | 201，返回 `user` + `personal_workspace_id` | 409 `EMAIL_ALREADY_EXISTS`；422 字段校验错误 |
| `POST /api/auth/login` | `email`、`password` | 200，返回 `access_token` | 401 |
| `POST /api/workspaces` | `name`（1–100 字） | 201，创建者自动成为 OWNER | 401；422 |

注意：注册时后端会自动创建一个个人 Workspace，所以新用户登录后列表里已经有一个了。

## 任务

1. **`frontend/lib/api.ts` 加两个函数**
    - `register(name, email, password)`：调 `/auth/register`，必须传 `auth: false`。想一想：如果不加，注册失败时会发生什么？（提示：看 `request()` 对 401 的处理）
    - `createWorkspace(name)`：调 `POST /workspaces`，返回新的 `Workspace`。可以参考已有的 `getWorkspace` 和 `toWorkspace`。
2. **新建注册页 `frontend/app/register/page.tsx`**
    - 四个输入框：姓名、邮箱、密码、确认密码。可以复制 `login/page.tsx` 当起点，样式直接复用。
    - 提交前先在前端检查：姓名不为空、密码 8–72 位、两次密码一致。不通过就不发请求。
    - 422：把 `error.fieldErrors` 里的信息显示在对应输入框下面。
    - 409：在邮箱下面提示“这个邮箱已经注册过，去登录？”，带一个去 `/login` 的链接。
    - 成功后：用同一个邮箱和密码调 `login()` → `setAccessToken(token)` → `router.replace("/workspaces")`。
3. **登录页和注册页互相链接**：登录页加“没有账号？注册”，注册页加“已有账号？登录”。
4. **“My workspaces” 页面加新建表单**（`frontend/app/workspaces/page.tsx`）
    - 一个名字输入框 + 创建按钮，调 `createWorkspace`，成功后跳到 `/workspaces/{新 id}/tickets`。
    - 出错时用 `describeError(error)` 显示。
    - 列表为空时显示“还没有 Workspace，先建一个”。
5. **后端加 2 个测试**（`backend/tests/test_auth_rbac.py`）
    - 注册时名字为空、邮箱格式不对、密码太短 → 422，并且 `details` 里三个字段都有错误。
    - 新用户注册 → 登录 → 只能看到自己的个人 Workspace → 新建一个 Workspace，角色是 OWNER → 在里面建 ticket 返回 201。
6. **更新文档**：README 的 Getting started 和 `docs/onboarding.zh-CN.md` 里各加一句“也可以在 /register 注册自己的账号”。

## 验收标准

- [ ] `cd backend && pytest -q` 全部通过，比原来多 2 个（26 passed）
- [ ] `cd frontend && npm run build` 通过
- [ ] 浏览器里用一个新邮箱注册，自动登录并看到自己的个人 Workspace
- [ ] 同一个邮箱再注册一次，看到“已注册”提示，不会被跳回登录页
- [ ] 密码只输 5 位或两次输入不一致，前端直接拦住，DevTools 的 Network 面板里没有发出请求
- [ ] 新建一个 Workspace，进去后侧边栏显示 OWNER，能建 ticket，也能删 ticket
- [ ] 用 carol 登录，她看不到你新建的 Workspace

## 提交

```bash
git add -A && git commit -m "Homework: register page and create workspace"
git push -u origin homework/register
```

然后在 GitHub 上开 PR 到 `main`，描述里贴上验收标准的勾选情况和一张注册页截图。

## 思考题（写在 PR 描述里）

1. 为什么前端已经检查了密码长度，后端还要再检查一遍？
2. 为什么 `register()` 要用 `auth: false`？
3. 注册成功后为什么要再调一次 `login()`，而不是让 register 接口直接返回 token？两种做法各有什么好处？
