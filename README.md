# 研究资料合成版本桶

此仓库提供本地授权演练用来源服务、协议样本和来源自身的测试，不包含收集客户端。全部机构、课程、账号、作品及观测均为合成资料。使用前阅读 [来源契约](docs/来源契约.md)。

Python 3.11及以上。安装固定依赖后，运行：

    python -m pip install -r requirements.txt
    python -m source.server --port 8765

服务默认绑定本机环境的8765端口，健康检查地址为http://127.0.0.1:8765/health。浏览器门户入口为契约所列资料端点。服务重启会重置演练状态。

来源测试：

    python -m unittest discover -s tests -v

独立容器可用docker build -t local-source .构建，docker run --rm -p 8765:8765 local-source启动。来源测试也可在构建镜像中运行：docker run --rm --network none local-source python -m unittest discover -s tests -v。容器使用非root用户，测试仅连接同容器回环源；笔记本WebSocket也在同容器内连接。

测试只检查来源如何发布资料与响应页面操作，不能证明收集、离线交付或业务解释已经实现。控制接口仅供本地演练。文档与代码没有真实服务凭据。
