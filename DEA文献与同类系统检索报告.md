# DEA 系统文献与同类项目检索报告

检索日期：2026-09-21  
检索范围：公开论文、出版社页面、GitHub 项目主页和在线 DEA 软件页面。  
说明：本报告用于产品定位、软著材料和专利撰写前的技术查新参考，不构成正式专利新颖性或法律意见。

## 一、结论先行

1. **DEA 方法和主要模型早已有大量文献。** CCR、BCC、SBM、超效率 SBM 和 Malmquist 指数均属于成熟方法，不能单独作为本系统的原创点。
2. **DEA 软件和网页系统也已经有人做过。** 最接近本系统的公开论文是 2021 年发表的 `deaR-shiny`，它是用于 DEA 效率和生产率分析的交互式网页应用，并支持传统 DEA、模糊 DEA 和 Malmquist 分解。
3. **本次公开检索没有发现与当前版本完全相同的组合。** 当前系统的组合特征是：中文科技风界面、CSV/Excel/Parquet 接入、公开 DEA 数据、径向 DEA + SBM + 超效率 SBM + Malmquist、非期望产出、结果数值审计、标杆与改进诊断、配置和结果导出。
4. **因此，系统可以继续申请软著，但不能把“DEA 算法”本身包装成独创。** 软著重点应放在真实代码、系统结构、数据处理流程、交互界面和可复现输出；若申请发明专利，应进一步提炼为具有明确技术流程和技术效果的系统方案，并进行正式专利查新。

## 二、最接近的已发表系统论文

### 1. deaR-shiny：最接近的网页化 DEA 系统

Benítez、Coll-Serrano 和 Bolós 于 2021 年发表论文 **“deaR-Shiny: An Interactive Web App for Data Envelopment Analysis”**，发表于 *Sustainability*，13(12), 6774，DOI：`10.3390/su13126774`。

该系统的特点包括：

- 以交互式网页应用形式提供 DEA 计算；
- 支持效率和生产率分析；
- 覆盖传统 DEA、模糊 DEA 以及 Malmquist 指数分解；
- 采用侧边栏、标签页、图形和结果表组织操作；
- 论文明确讨论了 DEA 软件、在线 DEA 解决方案和现有商业/非商业工具。

来源：[论文原文](https://www.mdpi.com/2071-1050/13/12/6774)

### 2. DEA 决策支持系统

Samoilenko 和 Osei-Bryson 于 2013 年发表 **“Using Data Envelopment Analysis (DEA) for monitoring efficiency-based performance of productivity-driven organizations: Design and implementation of a decision support system”**，发表于 *Omega*，41(1), 131–142，DOI：`10.1016/j.omega.2011.02.010`。

该论文说明 DEA 可以被集成为面向组织绩效监测和决策支持的系统，而不仅是一次性的数学计算脚本。

来源：[ScienceDirect 论文页面](https://www.sciencedirect.com/science/article/pii/S0305048312000382)

## 三、已有在线软件和开源项目

### 在线或商业软件

- [DEAOS](https://www.deaos.com/en-us/)：网页化 DEA 软件，支持 Excel/直接录入、多期数据、模型参数设置和多种格式导出。
- [MaxDEA](https://www.maxdea.com/Index_En.htm)：商业 DEA 软件，支持 CRS、VRS、方向选择和大规模数据分析。
- [DEAFrontier](https://www.deafrontier.net/deasoftware.html)：基于 Excel 的 DEA 插件。
- [EMS](https://www.holger-scheel.de/ems/)：较早的 DEA 软件，支持规模报酬、方向、超效率、Malmquist 和基准分析。

### GitHub / 开源项目

- [DEAPack](https://github.com/daopingw/DEAPack)：Python DEA 框架，覆盖 CCR/BCC、SBM、Malmquist、超效率、非期望产出以及标杆/松弛/目标等结果。
- [pyDEA](https://github.com/araith/pyDEA)：Python DEA 工具，提供图形界面、命令行和可导入接口。
- [SBM](https://github.com/Lx6uo/SBM)：Python 标准 SBM 和超效率 SBM 实现，包含非期望产出案例。项目 README 同时提示其实现仍需进行精度和复现性复核。

这些项目证明：底层 DEA 求解器、常见模型和部分结果诊断已经有开源实现。当前系统应避免直接复制其代码和界面，保留独立实现、来源记录和许可证合规证据。

## 四、模型方法的经典来源

| 模块 | 经典来源 | 与当前系统的关系 |
|---|---|---|
| CCR / CRS | Charnes, Cooper & Rhodes, 1978, DOI `10.1016/0377-2217(78)90138-8` | 径向 DEA、固定规模报酬 |
| BCC / VRS | Banker, Charnes & Cooper, 1984, DOI `10.1287/mnsc.30.9.1078` | 可变规模报酬和规模效率分解 |
| SBM | Tone, 2001, DOI `10.1016/S0377-2217(99)00407-5` | 直接处理投入冗余和产出不足 |
| 超效率 SBM | Tone, 2002, DOI `10.1016/S0377-2217(01)00324-1` | 区分多个效率值为 1 的 DMU |
| Malmquist | Caves, Christensen & Diewert, 1982 | 跨期生产率指数及距离函数思想 |

来源：[CCR 原文](https://www.sciencedirect.com/science/article/pii/0377221778901388)、[BCC 原文](https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.30.9.1078)、[SBM 原文](https://www.sciencedirect.com/science/article/abs/pii/S0377221799004075)、[超效率 SBM 原文](https://doi.org/10.1016/S0377-2217%2801%2900324-1)。

## 五、与当前系统的差异化分析

### 已经属于成熟或已有先例的部分

- CCR、BCC、SBM、超效率 SBM 和 Malmquist 的数学模型；
- 投入导向、产出导向、规模报酬设定；
- 参考标杆、权重、松弛变量和投影目标；
- 多期数据效率比较；
- 网页化上传数据、结果表和图表展示。

### 可以继续强化的差异化方向

- **数据—模型自动匹配**：根据字段结构判断单期数据或面板数据，并推荐径向 DEA、SBM 或 Malmquist；
- **模型可解释配置**：用中文业务语言说明投入、产出、非期望产出、方向和规模报酬，而不是只显示数学缩写；
- **计算结果审计**：自动检查效率范围、CCR/BCC 关系、规模效率上界、DMU 数量和不可行超效率状态；
- **可追溯分析链**：保存数据来源、字段配置、模型版本、求解状态、结果 CSV 和配置 JSON；
- **改进动作输出**：不仅给效率值，还给出投入压缩、产出提升、非期望产出削减、标杆和权重；
- **中文场景化数据资产**：提供医院、工业、能源、区域经济等公开数据集及字段解释；
- **面向软著的完整软件工程实现**：包括数据导入、校验、模型调度、结果缓存、导出和界面交互的完整代码链条。

## 六、对软著和专利的建议

### 软件著作权

可以继续申请。登记材料应以真实运行版本为基础，重点准备：

- 软件说明书；
- 操作流程和功能模块图；
- 用户界面截图；
- 源程序连续代码页；
- 版本号、开发完成日期和权利归属材料。

软著保护的是程序代码和文档表达，不保护 DEA 数学思想本身。

### 发明专利

不建议直接使用“基于 DEA 的效率评价系统”作为唯一创新点，因为同类系统和相关论文已经较多。更适合将权利要求集中到：

1. 面板/单期数据识别与模型自动选择方法；
2. 多模型统一配置、求解状态和结果审计方法；
3. 公开数据来源、字段语义和投入产出方向的自动映射方法；
4. 将效率结果转换为可执行投入压缩、产出提升和污染削减目标的方法；
5. 数据、模型、参数、校核记录和结果文件的一体化追溯机制。

这些方向仍需检索专利数据库并由专利代理师进行新颖性、创造性和实用性判断。

## 七、总体判断

**“有没有人做过？”——做过，且方法和系统层面都有先例。**  
**“有没有发过文献？”——有，最接近的是 deaR-shiny 网页 DEA 应用论文，以及 DEA 决策支持系统论文。**  
**“还能不能做？”——可以，但应从‘又一个 DEA 计算器’升级为‘可审计、可追溯、自动配置、可解释的 DEA 分析工作流系统’，并用真实代码和测试结果支撑软著或专利材料。**
