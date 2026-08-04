# CI/CD Setup Guide

## 架构概览

```
Azure DevOps                           OpenShift 集群
────────────                           ─────────────
 ado-pipelines.yml                     Tekton Pipeline
   │                                       │
   ├─ 1. 读 ADO Library (PAT)              ├─ clone  (git clone)
   ├─ 2. oc create secret (PAT→K8s)        ├─ build  (buildah bud --secret)
   ├─ 3. oc process Template → PR          └─ deploy (oc apply + rollout)
   └─ 4. 轮询 PipelineRun 状态
                                               │
                                          image-registry (内部)
                                               │
                                          Deployment rollout
```

## PAT 安全传递链路

```
ADO Variable Group (AES-256)
  → ADO agent 内存 (环境变量)
  → HTTPS → OpenShift API
  → K8s Secret (etcd, 静态加密)
  → Tekton Pod 内存 (env var)
  → buildah --secret → /run/secrets/ado_pat (tmpfs)
  → RUN --mount=type=secret 指令期间可用
  → RUN 结束立即销毁 (不写入任何镜像层)
```

## 前置条件

| 条件 | 说明 |
|------|------|
| OpenShift 4.12+ | 需要 OpenShift Pipelines Operator (Tekton) 已安装 |
| Azure DevOps | 项目已存在，Git repo 已托管 |
| 网络可达性 | ADO agent 能访问 OpenShift API server；OpenShift 节点能访问 Azure DevOps Git 和 Artifacts |
| ADO PAT | 有 Packaging (Read) 权限的 Personal Access Token |

> **内网注意**：如果 OpenShift 集群不对外暴露 API server，需在集群内或能访问内网的机器上运行 **自托管 ADO agent**，并将 `azure-pipelines.yml` 中 `pool: vmImage: ubuntu-latest` 改为你的自托管 pool 名。

---

## 一、初次部署（手动，仅需一次）

### 1.1 登录并创建项目

```bash
oc login https://api.<cluster>.example.com:6443 --token=<your-token>
oc new-project dac
```

### 1.2 替换占位符

编辑根目录 `Dockerfile`，将 `[org]` 和 `[feed]` 替换为你的 Azure DevOps 组织名和 Artifacts feed 名：

```dockerfile
# 示例：org=contoso, feed=dac-packages
RUN --mount=type=secret,id=ado_pat \
    ADO_PAT=$(cat /run/secrets/ado_pat) && \
    echo "@xdm:registry=https://pkgs.dev.azure.com/contoso/_packaging/dac-packages/npm/registry/" >> .npmrc && \
    echo "//pkgs.dev.azure.com/contoso/_packaging/dac-packages/npm/registry/:_authToken=${ADO_PAT}" >> .npmrc && \
    pnpm install && \
    rm .npmrc
```

pip 侧同理：

```dockerfile
RUN --mount=type=secret,id=ado_pat \
    ADO_PAT=$(cat /run/secrets/ado_pat) && \
    export PIP_EXTRA_INDEX_URL="https://contoso:${ADO_PAT}@pkgs.dev.azure.com/contoso/_packaging/dac-packages/pypi/simple/" && \
    pip-compile pyproject.toml --output-file=requirements.txt && \
    pip install -r requirements.txt
```

### 1.3 授权 pipeline SA 推送镜像

```bash
oc apply -f cicd/openshift/pipeline-sa-rbac.yaml
```

### 1.4 安装 Tekton Pipeline 定义

```bash
oc apply -f cicd/openshift/pipeline/pipeline.yaml
```

### 1.5 配置 ADO Variable Group

在 Azure DevOps Portal 中：

1. **Pipelines → Library → + Variable Group**
2. 命名 `dac-secrets`
3. 添加变量：

| 变量名 | 值 | 类型 |
|--------|-----|------|
| `OPENSHIFT_SERVER` | `https://api.ocp.example.com:6443` | 普通 |
| `OPENSHIFT_TOKEN` | `sha256~...` | **Secret** |
| `AZURE_PAT` | Azure DevOps PAT | **Secret** |

`OPENSHIFT_TOKEN` 获取方式：

```bash
# 使用已有用户
oc whoami -t

# 或创建专用 service account 的长期 token
oc create sa cicd-sa -n dac
oc create token cicd-sa -n dac --duration=0
```

### 1.6 创建 ADO Pipeline

1. Azure DevOps → Pipelines → New Pipeline
2. 选择你的 Git repo
3. 选择 **Existing Azure Pipelines YAML file**
4. 路径选 `cicd/azure-pipelines.yml`
5. 保存并运行

---

## 二、流水线运行流程

```text
Git Push (main/develop)
  │
  ▼
ADO Pipeline 触发
  │
  ├─ [Install oc CLI]      下载 OpenShift 客户端
  ├─ [Login OpenShift]     oc login + new-project (如不存在)
  ├─ [Sync Secret]         将 AZURE_PAT 写入 K8s Secret (ado-pat)
  ├─ [Submit PipelineRun]  oc process Template → oc apply PipelineRun
  └─ [Wait for complete]   每 10s 轮询 PipelineRun 状态，最长 30 分钟
                              │
                              ▼
                         Tekton Pipeline (OpenShift 上执行)
                              │
                              ├─ clone    git clone + checkout + submodule
                              ├─ build    buildah bud --secret=id=ado_pat,env=ADO_PAT
                              │              └→ 读取 Dockerfile 中 RUN --mount=type=secret
                              │              └→ 推送到 image-registry:5000/dac/dac-web:<git-sha>
                              └─ deploy   oc apply deployment.yaml
                                           oc set image dac-web=<new-image>
                                           oc rollout status --timeout=300s
```

---

## 三、工作区详解

### 3.1 `azure-pipelines.yml`

- **trigger**: 监听 `main`、`develop` 分支
- **变量源**: ADO Library Variable Group `dac-secrets`
- **构建 agent**: Microsoft-hosted `ubuntu-latest`（如需内网自托管，改为你的 pool 名）
- **输出**: 触发 OpenShift PipelineRun，等待其完成

### 3.2 Tekton `pipeline.yaml`

| Task | 镜像 | 工作 |
|------|------|------|
| `clone` | `alpine/git:latest` | 克隆仓库到 workspace |
| `build` | `buildah/stable:v1.38` | buildah bud + `--secret=id=ado_pat,env=ADO_PAT` + push |
| `deploy` | `openshift/origin-cli:latest` | oc apply deployment + oc set image + oc rollout status |

### 3.3 `pipelinerun-template.yaml`

OpenShift Template，接受 3 个参数：

| 参数 | 来源 | 示例 |
|------|------|------|
| `IMAGE_TAG` | `Build.SourceVersion` 短 SHA | `a1b2c3d` |
| `GIT_URL` | `Build.Repository.Uri` | `https://dev.azure.com/org/project/_git/repo` |
| `GIT_REVISION` | `Build.SourceVersion` 完整 SHA | `a1b2c3d4e5f6...` |

Template 处理后将生成 `PipelineRun`，命名为 `dac-web-pr-<IMAGE_TAG>`。

### 3.4 `deployment.yaml`

包含 4 个资源：

| 资源 | 说明 |
|------|------|
| `PersistentVolumeClaim` | 5Gi RWO 存储 (挂载到 `/app/storage`) |
| `Deployment` | 1 副本，健康检查 `/api/ping` |
| `Service` | 端口 8000 |
| `Route` | Edge TLS 终止 |

环境变量通过 `dac-web-config` Secret 注入（需手动创建，或通过 deploy task 扩展）：

```bash
oc create secret generic dac-web-config \
  --from-literal=POSTGRES_HOST=postgres.dac.svc \
  --from-literal=POSTGRES_PASSWORD=<password> \
  ...
```

### 3.5 `pipeline-sa-rbac.yaml`

授予 `pipeline` ServiceAccount 的 `system:image-builder` ClusterRole。
此 SA 由 OpenShift Pipelines Operator 自动创建，但需要额外授权才能推送镜像到内部 registry。

---

## 四、常用排错命令

```bash
# 查看 PipelineRun 状态
oc get pipelinerun -n dac

# 查看 PipelineRun 详情
oc describe pipelinerun dac-web-pr-<sha> -n dac

# 查看 TaskRun 日志
tkn pipelinerun logs dac-web-pr-<sha> -n dac -f

# 查看 build 任务日志
tkn taskrun logs dac-web-pr-<sha>-build -n dac -f

# 检查 PAT secret 是否存在
oc get secret ado-pat -n dac -o jsonpath='{.data.PAT}' | base64 -d | head -c 4 ; echo

# 检查镜像是否推送到 registry
oc get is dac-web -n dac
oc describe is dac-web -n dac

# 检查 Deployment 状态
oc describe deployment dac-web -n dac
oc get pods -n dac -l app=dac-web
```

---

## 五、安全要点

- **Dockerfile 第 11 行**: `rm .npmrc` 确保 `.npmrc` 不残留在镜像层中
- **Dockerfile 第 26-30 行**: PAT 仅在 `RUN --mount=type=secret` 指令生命周期内存在
- **不要在 RUN --mount 之外** `COPY` 或 `ADD` 任何 PAT 相关文件
- **K8s Secret** `ado-pat` 在每次 Pipeline 运行时被覆盖更新
- **ADO Variable Group** 中的 `AZURE_PAT` 标记为 secret 类型，日志自动遮蔽
