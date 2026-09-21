# 参考资料

`catalog.json` 是 literature/search.py 维护的元数据目录。每篇文献可按稳定 slug 保存 `ref/<slug>/paper.md`、阅读笔记、`source.json`、`repo.txt`；记录原始 URL、DOI/arXiv ID、版本、访问日期以及支持结论的原文定位。

PDF 与 `ref/<slug>/repo/` 默认忽略；单独的参考实现可克隆到 `refrepo/`。不要提交无权再分发的全文或私有资料。元数据可跨来源合并，全文核验状态由研究者明确记录。导入元数据永远标为 unverified-import，不能充当已在线检索的证明。
