# 公开数据说明

## 大学生学业效率数据（优先推荐）

- 文件：`uci_higher_education_dea_sample.csv`
- 来源：UCI Machine Learning Repository，数据集 697：Predict Students' Dropout and Academic Success
- 原始页面：https://archive.ics.uci.edu/dataset/697/predict%2Bstudents%2Bdropout%2Band%2Bacademic%2Bsuccess
- 原始规模：4424 名高等教育学生，包含选课、考核、通过课程数和学期平均成绩等字段
- 当前仓库样本：180 名学生，按 Dropout、Enrolled、Graduate 三类各取 60 条，并过滤两学期均有选课且至少有一项学业产出的记录，便于网页端快速演示
- 许可：CC BY 4.0。使用时应保留 UCI 数据集和论文引用：Realinho et al. (2021)，DOI: https://doi.org/10.24432/C5MC89
- 建议 DMU：`学生ID`
- 建议投入：`第一学期选课数`、`第二学期选课数`
- 建议期望产出：`第一学期通过课程数`、`第二学期通过课程数`、`第一学期平均成绩`、`第二学期平均成绩`
- 说明：该文件是从公开原始数据整理出的 DEA 演示样本，不代表学校正式评价结果，也不应作为个体奖惩依据。

## 中国医院效率数据

- 文件：`hospital_public.csv`
- 来源：GitHub `zhjx19/mathmodels-book` 仓库中的 `data/hospital.csv`
- 原始页面：https://github.com/zhjx19/mathmodels-book/blob/main/data/hospital.csv
- 原始数据：2011 年部分省级医院投入、产出及医疗废弃物指标
- 建议 DMU：`DMU`
- 建议投入：`床位数(万个)`、`卫技人员数(万个)`
- 建议期望产出：`诊疗人次数(万人次)`、`入院人数(万人)`
- 建议非期望产出：`医疗废弃物(万套)`

## 中国工业经济面板数据

- 文件：`economy_public.csv`
- 来源：GitHub `zhjx19/mathmodels-book` 仓库中的 `data/economy.csv`
- 原始页面：https://github.com/zhjx19/mathmodels-book/blob/main/data/economy.csv
- 数据结构：2005—2009 年各地区工业经济面板数据
- 建议 DMU：`DMUs`
- 建议时期：`Period`
- 建议投入：`Capital`、`Labor`
- 建议产出：`GIOV`
- 适用模块：Malmquist 指数、跨期效率变化和技术进步分析

数据仅用于系统演示和方法验证。正式发表、专利或软著材料使用前，应核对原始仓库的许可证、数据说明和引用要求，并保留来源信息。
