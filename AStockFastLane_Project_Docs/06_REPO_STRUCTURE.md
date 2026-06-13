# 06_REPO_STRUCTURE：推荐仓库结构

## 初始目录结构

```text
AStockFastLane/
  README.md
  requirements.txt
  .gitignore

  scripts/
    probes/
      test_eastmoney_news_probe.py
      test_cninfo_announcement_probe.py
      test_eastmoney_report_probe.py
      test_quote_probe.py

    providers/
      eastmoney_news_provider.py
      cninfo_announcement_provider.py
      eastmoney_report_provider.py
      quote_provider.py

    packs/
      build_fast_evidence_pack.py

    reports/
      generate_markdown_report.py

    utils/
      io_utils.py
      time_utils.py
      text_utils.py
      symbol_utils.py

  data/
    raw/
    cache/
    evidence/
    manual/
      watchlist_symbols.txt
      keyword_topics.json

  reports/

  docs/
    current_progress.md
    data_source_notes.md
    api_probe_logs.md
    architecture.md

  tests/
```

## 文件职责

### scripts/probes/

接口探针。只验证可用性，不进入正式流程。

### scripts/providers/

稳定封装。只放已经 probe 成功的接口。

### scripts/packs/

构建证据包。只读取 cache，不直接请求外部网络。

### scripts/reports/

生成报告。只读取 evidence pack。

### scripts/utils/

工具函数。不得包含业务主流程。

### data/raw/

保存带日期的原始抓取结果。

### data/cache/

保存最新结果，例如 `eastmoney_news_latest.json`。

### data/evidence/

保存 Evidence Pack。

### reports/

保存 Markdown 报告。

## .gitignore 建议

```gitignore
__pycache__/
*.pyc
.venv/
.env
.DS_Store

# 大体量数据，可按需要开启忽略
data/raw/*.json
data/cache/*.json
data/evidence/*.json
reports/*.md

# 但模板文件保留
!data/manual/*.txt
!data/manual/*.json
```
