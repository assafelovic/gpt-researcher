# 项目特定配置
PROJECT_NAME = researcher

# Namespace 配置（通常不需要修改，所有项目共享）
NAMESPACE_PRODUCTION = ivy
NAMESPACE_TESTING = ivy-testing

# Context 配置
CONTEXT_IVY = ivy      # production/testing 环境使用
CONTEXT_EDGE = edge  # edge 环境使用

K8S_BASE_DIR = .k8s/overlays
PUB_KEY_FILE = pub-key.prod.pem

# 导出变量以供子 Makefile 使用
export PROJECT_NAME
export NAMESPACE_PRODUCTION
export NAMESPACE_TESTING
export CONTEXT_IVY
export CONTEXT_EDGE
export K8S_BASE_DIR
export PUB_KEY_FILE

# 引入通用 Makefile
include scripts/common-makefile/Makefile

# 您可以在这里添加项目特定的其他命令

# 镜像仓库配置
IMAGE_REPO = registry.cn-shanghai.aliyuncs.com/ivysci/gpt-researcher

.PHONY: build custom-command

# 构建并推送镜像 (Target linux/amd64 for server deployment)
build:
	@echo "📦 Building and Pushing image (linux/amd64)..."
	@TAG=$$(git describe --tags --always --dirty); \
	echo "   Tag: $$TAG"; \
	echo ""; \
	docker buildx build --platform linux/amd64 \
		-t $(IMAGE_REPO):$$TAG \
		-t $(IMAGE_REPO):latest \
		--push .; \
	if [ $$? -eq 0 ]; then \
		echo ""; \
		echo "✅ Build & Push complete!"; \
		echo "   Image: $(IMAGE_REPO):$$TAG"; \
		echo ""; \
		echo "📝 To deploy this tag:"; \
		echo "   make set-tag env=testing tag=$$TAG"; \
	else \
		echo ""; \
		echo "❌ Build failed"; \
		exit 1; \
	fi

custom-command:
	@echo "这是项目特定的命令"