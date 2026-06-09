# PactBounty 生产部署与配置指南

本指南详细介绍了如何将 PactBounty 项目发布到生产环境或公开测试网。项目由三部分组成：
1. **Smart Contracts (Solidity/Foundry)**：部署在 EVM 测试网（如 Base Sepolia 或 Sepolia）。
2. **Backend (FastAPI)**：通过 Docker / Docker Compose / Railway / Render 部署。
3. **Frontend (Next.js)**：推荐部署在 Vercel 或通过 Docker 部署。

---

## 1. 智能合约部署 (EVM Testnet)

合约位于 `contracts/` 目录中。使用 Foundry 编译并运行部署脚本。

### 准备环境
首先在项目根目录下，将 `.env.example` 复制为 `.env`：
```bash
cp .env.example .env
```
编辑 `.env` 中的以下变量：
* `RPC_URL`: 目标测试网的 RPC 节点链接 (如 Infura, Alchemy 或 QuickNode)
* `PRIVATE_KEY`: 部署账户的私钥（确保有测试代币）

### 执行部署脚本
进入 `contracts` 目录并运行以下命令进行部署：
```bash
cd contracts
# 安装依赖
forge install foundry-rs/forge-std --no-commit
# 编译合约
forge build
# 运行部署脚本并广播到区块链
source ../.env
forge script script/Deploy.s.sol:Deploy --rpc-url $RPC_URL --broadcast --verify
```

部署完成后，脚本会输出以下合约的地址，请务必记录并填入根目录的 `.env` 中：
* `MOCK_USDC_ADDRESS`: MockUSDC 部署地址
* `AGENTIC_COMMERCE_ADDRESS`: AgenticCommerce (Escrow 托管) 合约部署地址

---

## 2. 后端部署 (FastAPI)

后端支持 Mock 模式与 Real 真实接入模式。

### 2.1 环境变量配置
在 `.env` 中填入以下真实密钥来激活 Cobo Agentic Wallet (CAW) 和 GLM-5.1 (Z.AI) 接入：

```bash
# 激活真实模式
CAW_MODE=real
LLM_MODE=real

# Cobo Agentic Wallet 配置
AGENT_WALLET_API_URL=https://api.agenticwallet.cobo.com
AGENT_WALLET_API_KEY=your-cobo-api-key
AGENT_WALLET_WALLET_ID=your-cobo-wallet-id

# GLM-5.1 驱动 Z.AI 配置
ZAI_API_KEY=your-z-ai-api-key
ZAI_BASE_URL=https://api.z.ai/api/paas/v4/
ZAI_MODEL=glm-5.1

# 合约与链配置
RPC_URL=your-rpc-url
PRIVATE_KEY=your-deployer-private-key
MOCK_USDC_ADDRESS=0x...
AGENTIC_COMMERCE_ADDRESS=0x...
```

### 2.2 部署选项 A：使用 Docker Compose
我们提供了 `docker-compose.prod.yml` 配置文件，该文件会自动拉取 GitHub Container Registry (GHCR) 中的最新镜像：

```bash
# 运行生产容器
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

### 2.3 部署选项 B：云托管 (Railway / Render)
因为后端是标准 Dockerized FastAPI 应用，你可以极易地在 Railway 或 Render 部署：
1. **关联 GitHub 仓库**：在平台上新建服务，指向你的 Public 仓库。
2. **构建设置**：
   * Root Directory 设为 `backend`。
   * 选择以 Dockerfile 构建（平台会自动识别 `backend/Dockerfile`）。
3. **环境变量**：在平台控制面板中导入上述 `.env` 的所有配置。

---

## 3. 前端部署 (Next.js)

### 3.1 部署选项 A：Vercel（推荐 ⭐️）
Next.js 由 Vercel 团队开发，使用 Vercel 托管能获得开箱即用的高性能与完美兼容。

1. 访问 [Vercel](https://vercel.com) 并创建一个新项目（Import Git Repository）。
2. 选择导入你的 `pactbounty` 仓库。
3. **配置参数**：
   * **Root Directory**：设置为 `frontend`。
   * **Framework Preset**：Next.js (自动识别)。
   * **Build Command**：`npm run build`。
   * **Install Command**：`npm ci`。
4. **Environment Variables**：
   添加 `NEXT_PUBLIC_API_BASE_URL` 环境变量，其值指向你已部署好的**后端公网 API 地址**（例如 `https://pactbounty-backend.railway.app`）。
5. 点击 **Deploy** 部署。

### 3.2 部署选项 B：Docker 自建部署
如果您使用自己的服务器运行前端：
1. 使用 `docker-compose.prod.yml`。
2. 确保将 `NEXT_PUBLIC_API_BASE_URL` 替换为你的后端实际域名。

---

## 4. 版本管理工作流

本项目接入了完备的 GitHub Actions 持续集成与发布：
* **每次 Commit / Pull Request**：CI 自动运行（`.github/workflows/ci.yml`），校验合约测试、后端 Python 测试和前端 TypeScript 构建，确保代码质量。
* **发布新版本**：
  当准备好发布新版本时，推送一个 `v*` 格式的 Git 标签：
  ```bash
  git tag v1.0.0
  git push origin v1.0.0
  ```
  GitHub Actions 会自动：
  1. 生成对应的 GitHub Release 和 Changelog 变更日志。
  2. 构建生产环境 Docker 镜像，推送到 GitHub Container Registry (GHCR) 的包管理仓库：
     * 后端镜像：`ghcr.io/your-github-username/pactbounty-backend:v1.0.0`
     * 前端镜像：`ghcr.io/your-github-username/pactbounty-frontend:v1.0.0`
