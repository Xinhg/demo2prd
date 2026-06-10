# proto-to-requirement Skill Suite 安装说明

本压缩包包含三段式需求工程 skill：

- `proto-to-requirement`：Stage 1，解析 Mockitt/MoDao 原型导出。
- `proto-pm-interviewer`：Stage 2，基于解析证据采访产品经理。
- `bdd-engineering-prd-writer`：Stage 3，编写 BDD 工程版 PRD。

同时包含 Stage 1 所需的 Python runtime：

- `proto_to_requirement/`
- `pyproject.toml`
- `uv.lock`
- `tests/`

## 环境要求

- Python 3.10+
- `uv`
- Codex/Claude 等支持本地 skill 目录的 agent 环境

本项目命令统一使用 `python3`，依赖和运行统一使用 `uv`。

## 解压

```bash
unzip proto-to-requirement-skill-suite.zip -d proto-to-requirement-skill-suite
cd proto-to-requirement-skill-suite
```

## 验证 runtime

```bash
uv run python3 -m proto_to_requirement.cli --help
uv run pytest
```

如果这两个命令通过，说明解析器 runtime 和测试环境正常。

## 安装到 Codex skills 目录

将三个 skill 目录复制到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R proto-to-requirement ~/.codex/skills/
cp -R proto-pm-interviewer ~/.codex/skills/
cp -R bdd-engineering-prd-writer ~/.codex/skills/
```

重启或刷新 Codex 后，三个 skill 应可被发现。

## 保留 runtime 目录

`proto-to-requirement` 的解析阶段会调用本包中的 Python runtime。建议把解压后的完整目录保留在一个固定位置，例如：

```bash
~/codex-skill-runtimes/proto-to-requirement-skill-suite
```

如果安装到当前 Codex，推荐 runtime 目录为：

```bash
~/.codex/skill-runtimes/proto-to-requirement-skill-suite
```

注意：`~/.codex/skills/proto-to-requirement` 这个 skill 目录通常只包含 `SKILL.md` 和参考材料，不应假设解析器 Python 包一定在该目录内。

之后运行解析命令时，在该目录中执行：

```bash
uv run python3 -m proto_to_requirement.cli <prototype_dir> --output <output_dir>
```

示例：

```bash
uv run python3 -m proto_to_requirement.cli /path/to/mockitt-export --output output/mockitt-export
```

## 使用顺序

1. 使用 `proto-to-requirement` 解析 Mockitt/MoDao 原型导出，得到：
   - `prototype-analysis.md`
   - `structured-data.json`
   - `completeness-report.json`
   - `requirements.md` 草稿
2. 使用 `proto-pm-interviewer` 基于解析证据和辅助材料生成采访问题，并产出 PM 采访报告。
3. 使用 `bdd-engineering-prd-writer` 整合解析证据、PM 确认、人工 PRD 和辅助材料，生成最终 `bdd-engineering-prd.md`。

## 注意事项

- Stage 1 目前只支持本地 Mockitt/MoDao 纯数据导出。
- 不支持 Axure、Figma、在线原型 URL、浏览器渲染或视觉模型分析。
- 不要把 Stage 1 的 `requirements.md` 草稿当成最终 BDD 工程 PRD。
- 最终 PRD 中的确定需求必须有来源：解析证据、PM 确认、人工 PRD、辅助材料或仓库证据。
- P0 未确认项不能写成验收标准，必须先确认或标记为阻塞。
