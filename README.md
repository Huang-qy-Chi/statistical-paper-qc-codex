# Statistical Paper QC for Codex

[English](READMEen.md) | **简体中文**

面向统计学论文的 Codex 辅助质量检查技能，检查正文与补充材料的一致性、数值声明、证明假设和证明缺口，并保留证据与覆盖记录。

这是供 Codex 执行的审查流程，不是独立的自动审稿程序，也不提供形式化证明保证。辅助脚本只负责 PDF 提取、页面渲染与台账校验。

## 来源与授权状态

本项目改编自 [BIG-S2/statistical-paper-qc](https://github.com/BIG-S2/statistical-paper-qc) 的 `skills/jasa-acs-qc/SKILL.md`。原项目提供 Claude 示例；本版本增加 Codex 运行指引、跨平台工具、检查台账、条件化统计判定和合成测试。

本版本准备于 2026-10-16。所依据的上游本地快照未发现许可证文件。

## 功能

| 模块 | 范围 |
| --- | --- |
| A | 正文与补充材料的引用、表格、描述和假设一致性 |
| B | 合计、百分比、统计量、模拟结果和数值声明复算 |
| C | 可选的期刊结构检查，须核实当前期刊政策 |
| D | 逐定理检查假设、推导、边界、反例及外部结果使用 |

台账区分 `pending`、`verified`、`finding`、`inconclusive`、`not_applicable`。经验收敛率、反推模拟次数及参数拟合等诊断线索不自动作为已证实错误。公式问题必须核对页面图像；数值问题保留复算证据。

## 环境与依赖

已测试环境为 Windows、Python 3.12.14。依赖版本固定为本次实际测试版本；其他系统和 Python 版本尚未验证。若某版本无适配 wheel，不应假定安装成功。

优先使用 Codex 提供的工作区 Python 和依赖，无须重复安装。普通 Python 环境可在仓库根目录创建隔离环境：

Windows PowerShell：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe skills/statistical-paper-qc/scripts/qc_tools.py probe
```

macOS 或 Linux（命令可移植性设计，尚未实机验证）：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python skills/statistical-paper-qc/scripts/qc_tools.py probe
```

`probe` 只检查包和命令是否可发现，不执行 OCR，也不证明全部功能正常。依赖文件包含 PyMuPDF（首选提取和渲染）、pypdf（提取回退）、NumPy（数值复算）和 python-docx（Word 生成）。

Poppler 的 `pdftoppm` 是可选渲染回退，不是 PyMuPDF 正常工作时的必需项。Word 视觉验收还需要 Codex 文档工具或可用的 LibreOffice 渲染环境；这些系统组件不能由 requirements.txt 安装。缺失时交付 Markdown，Word 草稿仅作未验收中间文件。扫描件需另行 OCR。

## 安装到 Codex

下载仓库后，只复制 `skills/statistical-paper-qc` **整个目录**到 Codex 能发现的技能位置，不要仅复制 SKILL.md，也不要将整个仓库误当成一个技能。

项目级安装可使用 `.agents/skills/statistical-paper-qc`。用户级目录按安装环境使用 `~/.agents/skills/statistical-paper-qc`；本版本也已在当前 Codex 桌面环境的 `~/.codex/skills/statistical-paper-qc` 中验证加载。[官方技能文档](https://learn.chatgpt.com/docs/build-skills)

例如在 PowerShell 中安装到官方文档列出的用户级目录（目标存在时先检查，避免覆盖已有版本）：

```powershell
$skillRoot = Join-Path $HOME '.agents/skills'
$destination = Join-Path $skillRoot 'statistical-paper-qc'
if (Test-Path -LiteralPath $destination) { throw 'Skill already exists; inspect it before updating.' }
New-Item -ItemType Directory -Path $skillRoot -Force | Out-Null
Copy-Item -LiteralPath './skills/statistical-paper-qc' -Destination $destination -Recurse
```

在新聊天输入 `$statistical-paper-qc`；若没有出现，重启 Codex 并检查目录。依赖安装在 `.venv` 时，在审查请求中提供该解释器的绝对路径；复制技能不会自动复制或安装 Python 环境。

## 使用

```text
请使用 $statistical-paper-qc 检查 main.pdf 和 supp.pdf。
编号 PAPER-001，运行 A、B、D，跳过期刊结构模块 C。
请用中文报告，公式问题先查看原页，数值问题保存复算代码和输出。
记录已检查、未检查和证据不足的项目，输出到本工作区 outputs。
默认生成 Word 并核验排版；无法核验时交付 Markdown 并说明限制。
```

可以只检查指定表格、定理或章节。无需自动切换到高成本模型。复杂数学结论仍须逐步核实；有限数值实验不能证明一般定理。

手工调用辅助工具示例（`python` 应换成所选环境解释器）：

```bash
python skills/statistical-paper-qc/scripts/qc_tools.py prepare --pdf main.pdf --out work/main
python skills/statistical-paper-qc/scripts/qc_tools.py render --pdf main.pdf --pages 1 2 --out work/main-images
python skills/statistical-paper-qc/scripts/qc_tools.py check-ledger --ledger work/qc-ledger.json
```

输出目录必须为空，防止覆盖旧证据。工具写入一基 PDF 页码和 SHA-256；纸面页码需要人工核对。台账格式见 [ledger.md](skills/statistical-paper-qc/references/ledger.md)。

## 可复现测试

从仓库根目录执行，无需 Codex 登录或 API 密钥。以下命令沿用前面创建的 `.venv`，无需激活环境。

Windows PowerShell：

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements-test.txt
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

macOS 或 Linux：

```bash
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m unittest discover -s tests -v
```

测试自动在仓库 `work/` 下的临时目录生成合成 PDF、提取文本并检查辅助工具，不依赖本机用户名或先前任务目录；仓库目录需可写。运行结束清理临时文件，可以重复运行。没有 `pdftoppm` 时，仅跳过对应的可选回退测试并显示原因，其余测试仍应运行。

需要保留材料做人工或模型审查时（将 `python` 替换为上述 `.venv` 解释器；使用 Codex 自带环境时替换为其解释器路径）：

```bash
python tests/synthetic.py --out work/synthetic
```

该命令拒绝覆盖非空目录。PDF 生成采用固定元数据，并附带 SHA-256 清单；固定环境中应可重复生成相同字节。换依赖版本后不承诺相同 PDF 哈希。

请将生成的 main.pdf 和 supp.pdf 交给技能，并使用 [审查请求](examples/synthetic/audit-request.txt)。[expected.json](examples/synthetic/expected.json) 是预期结果，供人工验收；不要把它作为待评估模型的输入。

合成案例包含 3 个问题（合计错误、引用不存在的 Table S9、严格正性定理在零点失败）和 3 个正常对照（33.3% 舍入、不同实验重复次数、二项式展开）。不规定模型必须使用相同问题 ID 或措辞。

自动测试验证 PDF 工具、台账边界及合成材料中的可核对事实，**不会自动评价 Codex 是否正确审稿**。人工检查应核对证据、6 项范围覆盖和误报情况，不只比较输出字词。Word 生成和排版不是本测试套件的通过条件。

## 已知限制与资料处理

- 本次只在 Windows 和上述依赖环境验证；合成案例不能代表真实论文准确率。
- 本机 Word 生成已验证，视觉验收因缺少 LibreOffice 未完成；保留降级路径。
- 台账验证检查结构、输入哈希与声明的证据文件存在，不保证数学结论真实，也不保证页码未超出文档；仍需核对原页。
- 不在此仓库提交真实论文、补充材料、提取文本、数据或报告。`.gitignore` 只是防误提交辅助，发布前仍须检查文件。
- 本地执行工具不等于模型离线运行；选取的内容仍会发送至当前模型服务。仅处理获准在该环境使用的材料。

## 仓库布局

```text
README.md
READMEen.md
requirements.txt
requirements-test.txt
.gitignore
skills/statistical-paper-qc/
  SKILL.md
  agents/openai.yaml
  references/modules.md
  references/ledger.md
  scripts/qc_tools.py
tests/synthetic.py
tests/test_qc_tools.py
examples/synthetic/audit-request.txt
examples/synthetic/expected.json
```
