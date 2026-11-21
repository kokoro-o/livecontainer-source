# 个人 LiveContainer 应用源

将本仓库 `source.json` 的 raw 地址添加到 LiveContainer 的 Sources。聚合源每 6 小时检查一次 GitHub 正式版 Release，可在 Actions 手动运行。IPA 下载链接指向原项目；One 和 WQ Files 使用原作者的源。

收录 GestaltX、3106、WQManager、iPadn（标准版）、HGhubX、One、WQ Files、AniCh、Beans Music、Cloudn、Erosion-CN、Kazumi、Regitela、Henge、placard、Camlo 和 Andarium（Kernarium 项目）。

应用能否运行取决于系统版本、签名和所需权限；系统工具尤其需要核对其项目文档。源更新不会自动安装应用。

运行 `python3 update.py` 可本地更新。某个项目暂时失败时保留旧条目，工作流显示失败以便检查；多 IPA 时需要在脚本中指定选择规则。
