# 发布指南

本指南说明如何将 `moi-python-sdk` 发布到 PyPI，让用户可以通过 `pip install moi-python-sdk` 直接安装。

## 前置准备

1. **注册 PyPI 账号**
   - 访问 https://pypi.org/account/register/ 注册账号
   - 如果使用测试环境，访问 https://test.pypi.org/account/register/

2. **安装构建工具**
   ```bash
   pip install build twine
   ```

3. **配置 PyPI 认证**
   
   创建 `~/.pypirc` 文件（可选，也可以使用环境变量）：
   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = pypi-你的API令牌

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-你的测试API令牌
   ```

   或者使用环境变量：
   ```bash
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-你的API令牌
   ```

## 发布步骤

### 1. 更新版本号

在 `setup.py` 和 `pyproject.toml` 中更新版本号：

```python
# setup.py
version="0.1.1",  # 更新版本号
```

```toml
# pyproject.toml
version = "0.1.1"  # 更新版本号
```

### 2. 构建分发包

```bash
# 清理旧的构建文件
rm -rf dist/ build/ *.egg-info

# 构建源码包和wheel包
python -m build
```

这会在 `dist/` 目录下生成：
- `moi-python-sdk-0.1.0.tar.gz` (源码包)
- `moi_python_sdk-0.1.0-py3-none-any.whl` (wheel包)

### 3. 检查构建结果（可选）

```bash
# 检查包的内容
twine check dist/*
```

### 4. 测试发布到 TestPyPI（推荐）

先发布到测试环境验证：

```bash
twine upload --repository testpypi dist/*
```

然后测试安装：

```bash
pip install --index-url https://test.pypi.org/simple/ moi-python-sdk
```

### 5. 发布到正式 PyPI

确认无误后，发布到正式 PyPI：

```bash
twine upload dist/*
```

### 6. 验证安装

发布后等待几分钟，然后测试：

```bash
pip install moi-python-sdk
```

## 自动化发布（使用 GitHub Actions）

可以创建 `.github/workflows/publish.yml` 来自动化发布流程：

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## 版本号规范

建议遵循 [语义化版本](https://semver.org/)：
- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

例如：`1.2.3` → `1.2.4` (bug修复) → `1.3.0` (新功能) → `2.0.0` (重大变更)

## 常见问题

### 1. 包名已存在

如果 `moi-python-sdk` 已被占用，需要：
- 在 PyPI 上搜索确认
- 如果确实被占用，修改 `setup.py` 和 `pyproject.toml` 中的 `name` 字段

### 2. 上传失败：认证错误

- 检查 API token 是否正确
- 确保 token 有上传权限
- 尝试使用 `--verbose` 查看详细错误

### 3. 版本号冲突

- 每次发布必须使用新的版本号
- 不能重复使用已发布的版本号

## 参考资源

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI 文档](https://pypi.org/help/)
- [Twine 文档](https://twine.readthedocs.io/)

