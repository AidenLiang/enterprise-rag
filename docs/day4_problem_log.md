# Enterprise RAG --- Day 4 Problem Log

> **记录范围：** Day 4 查询改写与证据检查的验证，以及多 Chunk
> 上下文生成实验。本文记录本次实际观察到的行为和阶段性结论，不把尚未核实的推断写成确定事实。

## Day 4 goal

-   验证查询改写能否在初次检索不足时帮助系统恢复。
-   检查证据评估是否能区分"提到了相关主题"和"足以回答问题"。
-   验证系统在证据不足时能否避免编造答案。
-   减少 Reranker 选错或只选中部分证据时，对最终回答造成的影响。

## Work completed / confirmed

1.  运行了 `app.evaluation.test_agentic_rag`，检查 5 个问题的检索、Agent
    评估、Reranker 选择和最终回答。
2.  保留了 Agent 的查询改写、证据评估、有限重试和历史记录流程。
3.  验证了多 Chunk 上下文生成方案：将 Reranker 选中的 Chunk
    放在上下文最前面，再附加其他检索候选；每段证据标注页码和 Chunk
    编号，并继续使用原来的 `build_prompt()`。
4.  对比了生成答案是否包含预期事实、证据是否支持答案，以及 Reranker
    是否选中预期位置。
5.  决定将多 Chunk 上下文方案作为当前阶段性基线，Day 4
    到此结束；暂不继续调整 Prompt、检索参数或 Agent 逻辑。

## Problem log

### 1. 证据评估器可能把"证据不足"判断得过于严格

-   **Observed behavior：** HbA1c 用药调整比例和再入院率问题中，Agent
    的证据评估两次都认为证据不足，触发了查询改写；但累计检索结果中仍包含可能回答问题的候选文本。
-   **Impact：** `Agent success: False`
    不一定代表最终答案一定错误；它反映的是 Agent
    的证据评估未通过，而最终生成质量需要单独检查。
-   **Status note：** 目前保留该行为，不在 Day 4
    继续改动。后续应分别评估 Agent 的证据判断与最终答案正确性。

### 2. Reranker 可能选中相邻但不完整的 Chunk

-   **Observed behavior：** "How was early hospital readmission defined
    in the study?" 的候选中，Page 2 / Chunk 13 明确包含定义；Reranker
    却选择了 Page 2 / Chunk 14。Chunk 14
    是相邻的延续内容，主要补充如何检查患者记录以及为什么采用 30 天标准。
-   **Cause / interpretation：**
    候选文本存在语义连续性，模型可能选中与问题相关、但没有完整承载答案的段落。
-   **Fix direction tested：** 将选中的 Chunk
    放在生成上下文第一位，同时保留其他候选，降低单一 Chunk
    选择错误导致关键信息丢失的风险。
-   **Status：** 本次多 Chunk 生成可以回答这道题，但 Reranker 的 Chunk
    级选择仍不完美。

### 3. 单 Chunk 生成会丢失其他候选中的有效证据

-   **Observed behavior：** 之前只把 Reranker 选中的单个 Chunk
    交给生成模型时，部分回答遗漏了定义或关键信息。
-   **Change tested：** 先放入 Reranker
    选中的候选，再按原顺序附加其他候选，并用 `[Evidence | Page | Chunk]`
    标注来源。
-   **Observed result：**
    本次"早期再入院定义"问题能够从组合上下文中得到正确回答，说明保留其他候选对最终生成有帮助。
-   **Trade-off：** 上下文更长，模型可能混淆不同段落的数字或语义；多
    Chunk 不是无条件更好，仍需检查答案与证据之间的对应关系。

### 4. "HbA1c 开单后有多少患者调整用药"暴露了评估器与生成器判断不一致

-   **Observed behavior：** Agent 认为证据不足，但最终生成答案给出了
    55.0%；本次答案检查通过。
-   **Evidence detail：** 检索文本同时提到未进行 HbA1c 检测时的
    42.5%、检测后相关的 55.0%，以及 HbA1c 大于 8% 时的
    65.0%。这些数字对应不同条件，不能互换。
-   **Risk：** 只检查答案里是否出现
    `55.0%`，不足以证明数字与问题中的人群条件对应正确。
-   **Status：**
    本次记录结果，不再为了这一题继续调整系统；后续若重新评估，应检查数字、条件和原文之间的对应关系。

### 5. 再入院率问题出现数字与人群对应关系不稳定

-   **Observed behavior：** 最终回答把 8.7% 归给有 HbA1c 测量的人群，把
    9.4% 归给没有测量的人群；答案包含两个预期数字，但"Expected facts
    present in evidence"检查失败，因此最终结果为 FAIL。
-   **Interpretation：**
    数字都出现不等于答案完全正确。评估还必须确认每个数字对应的患者组别是否与原文一致。
-   **Next verification:** 如未来继续优化，应回到论文原文核对 9.4% 和
    8.7%
    的顺序及各自对应的人群，再更新测试预期；本次不凭猜测更改答案标准。

### 6. 评估指标衡量的是不同环节，不能相互替代

-   **Observed behavior：** 本次 5 道题均检索到了预期位置对应的证据，但
    Reranker Accuracy 和 Generation Accuracy 都是 0.8。
-   **Meaning:**
    -   `Expected evidence retrieved` 检查预期位置是否出现在检索候选中。
    -   `Rerank Accuracy` 检查最终选择的位置是否命中预期位置。
    -   `Generation Accuracy`
        检查最终答案及证据检查是否满足当前测试标准。
-   **Conclusion：** 检索到正确证据，不代表 Reranker 一定选对；选对
    Chunk 也不代表生成答案一定正确。三项结果应分开记录。

### 7. 小规模测试结果容易波动

-   **Observed behavior：** 当前测试集只有 5
    道题，每道题的成败会让准确率变化 0.2。
-   **Impact：** 0.8 只能作为这 5
    道测试题上的阶段性结果，不能直接声称系统整体准确率达到 80%。
-   **Status：** Day 4
    不扩充测试集、不继续追逐单次分数；后续对照实验时固定同一测试集和评估规则。

## Evaluation record --- keep separate runs separate

### Current selected run

  ---------------------------------------------------------------------------------------------
  Metric                                      Result Interpretation
  --------------------- ---------------------------- ------------------------------------------
  Total questions                                  5 当前小规模测试集

  Expected evidence                              5/5 5 道题都检索到了预期位置的证据
  retrieved                                          

  Rerank Accuracy                          0.8 (4/5) 1 道题没有选中预期 Chunk

  Generation Accuracy                      0.8 (4/5) 1 道题因证据与数字对应关系检查失败而未通过
  ---------------------------------------------------------------------------------------------

**Important:** 上表只记录本次运行。不要把不同
Prompt、不同代码版本或不同评估规则下的分数混在一起比较。

## Baseline decision and repository status

-   **Selected baseline:** 多 Chunk 上下文生成------Reranker 选中的
    Chunk 排在最前面，其他检索候选继续提供给生成模型。
-   **Reason:** 在本次小规模测试中，生成准确率达到 0.8；同时缓解了单
    Chunk 缺少完整证据的问题。当前收益足以支持暂时保留该版本。
-   **Not claimed:** 这并不证明多 Chunk 在所有任务上都优于单
    Chunk，也不代表所有评估问题均已解决。
-   **Change freeze:** Day 4 结束后，暂不继续修改 Agent、Reranker
    Prompt、检索参数或评估逻辑；把未解决项记录下来，避免反复返工。
-   **Repository status:** 本文档是待提交的日志文件。是否已提交或推送到
    GitHub，以本地 `git status`、提交记录和 `git push` 结果为准。

## Day 4 conclusion

Day 4 完成了查询改写与证据检查流程的验证，并测试了多 Chunk
上下文生成。当前基线在 5 道题上得到 **Expected evidence retrieved =
5/5、Rerank Accuracy = 0.8、Generation Accuracy =
0.8**。主要遗留问题是证据评估与最终生成判断不一致、Reranker
可能选中相邻但不完整的 Chunk，以及数字和人群条件的对应关系需要严格核验。

**本日决定：保留当前多 Chunk 版本，结束 Day 4，不再为单道题持续返工。**
