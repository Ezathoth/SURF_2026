# MPM 生物标志物数据库 · 项目规范书 (Project Specification)

**版本**:v0.2(Phase 2 完成)
**日期**:2026-07-07
**项目根目录**:`mpm_biomarker_db/`
**许可**:数据 CC BY 4.0 · 代码 MIT

---

## 1. 项目定位

### 1.1 目标

面向恶性胸膜间皮瘤(Malignant Pleural Mesothelioma, MPM)研究社区,构建一个**学术开源、可扩展、可追溯**的综合性生物标志物数据资源平台,定位类比 cBioPortal 之于间皮瘤:

- **整合公共数据**:把分散在 TCGA、UniProt、Open Targets、GEO、DepMap、ChEMBL、CIViC、OncoKB、ClinicalTrials.gov、Cellosaurus 等 10+ 源的 MPM 相关证据统一到一个 schema
- **多源合并**:同一 biomarker 挂多条外部引用,通过一张视图即可跨源检索
- **保留可追溯性**:每条记录都能回溯到数据源版本 + 抓取时间 + 原始 payload
- **优先分子标志物 + 试验/药物**:本阶段聚焦分子层面 + 临床试验 + 药物,液体活检/影像组学/病理组学骨架保留、下期填数据

### 1.2 分类框架

采用 **FDA-NIH BEST 框架**(Biomarkers, EndpointS, and other Tools),7 类临床用途:诊断 / 监测 / 药效 / 预测 / 预后 / 安全 / 易感性。当前 seed 数据仅覆盖 **诊断** + **预后** 两类,其余类别 schema 保留、下期扩充。

### 1.3 亚型分层(强制)

每条 evidence 记录必须携带 `subtype_scope` 字段,取值 `pan_mpm` / `epithelioid` / `sarcomatoid` / `biphasic` / `other` / `unspecified`。亚型特异性效应量以独立行存,不折叠。

### 1.4 证据分级(A-F)

| 级别 | 定义 |
|---|---|
| A | 独立队列验证或 meta 分析(n ≥ 200) |
| B | 大单中心队列(n ≥ 100) |
| C | 小队列(n < 100) |
| D | 病例系列 / 病例报告 |
| E | 临床前(in vitro / in vivo) |
| F | 生信 / in silico |

---

## 2. 18 seed 基因

所有 V2 阶段数据抓取都以下述 18 个 seed 基因为过滤锚点:

| Symbol | Entrez | UniProt | 染色体 | MPM 中角色 | 别名 |
|---|---|---|---|---|---|
| BAP1 | 8314 | Q92560 | 3p21.1 | TSG | — |
| CALB2 | 794 | P22676 | 16q22.1 | 诊断标志(calretinin) | — |
| CD274 | 29126 | Q9NZQ7 | 9p24.1 | 免疫治疗预测 | PD-L1 |
| CDKN2A | 1029 | P42771 | 9p21.3 | TSG | p16 |
| EZH2 | 2146 | Q15910 | 7q35 | TSG(合成致死靶点) | — |
| EFEMP1 | 2202 | Q12805 | 2p25.3 | 血清标志物 | FBLN3, fibulin-3 |
| HEG1 | 57493 | Q9ULI3 | 3q21.1 | 表面糖蛋白 | — |
| KRT5 | 3852 | P13647 | 12q13.13 | 诊断标志(CK5/6) | — |
| MSLN | 10232 | Q13421 | 16p13.3 | 治疗靶点 + 血清标志物 | mesothelin |
| MTAP | 4507 | Q13126 | 9p21.3 | 9p21 共缺失 | — |
| NF2 | 4771 | P35240 | 22q12.2 | TSG(Hippo 通路) | merlin |
| PDPN | 10630 | Q86YL7 | 1p36.21 | 诊断标志(D2-40) | — |
| SLC2A1 | 6513 | P11166 | 1p34.2 | 代谢标志 | GLUT1 |
| SPP1 | 6696 | P10451 | 4q22.1 | 血清标志物 | osteopontin |
| TERT | 7015 | O14746 | 5p15.33 | 端粒 | — |
| THBD | 7056 | P07204 | 20p11.21 | 诊断标志(thrombomodulin) | — |
| WT1 | 7490 | P19544 | 11p13 | 诊断标志 | — |
| YAP1 | 10413 | P46937 | 11q22.1 | Hippo 效应因子 | — |

---

## 3. 数据源与集成

### 3.1 Phase 1 已入(6 源,20 biomarker,67 evidence)

| 源 | 用途 | 已入 xrefs |
|---|---|---|
| UniProt | 蛋白级注释 | 19 |
| Open Targets | 靶点-疾病关联评分 | 5 |
| GDC / TCGA-MESO | 突变/CNV 频率 | 18 |
| GEO | 表达数据集 | 26 |
| 手工文献 seed | 诊断/预后经典证据 | 67 evidence 记录 |
| Cellosaurus(Phase 2 扩展前 seed) | 细胞系映射 | — |

### 3.2 Phase 2 新入(6 源,877 - 68 = 809 新 xrefs)

| 源 | API | 目标表 | 已入行数 |
|---|---|---|---|
| **ClinicalTrials.gov v2** | `clinicaltrials.gov/api/v2/studies` | `clinical_trials` + `interventions` + `external_references(source='clinicaltrials')` | 385 试验 / 34 biomarker xrefs |
| **Cellosaurus** | REST + figshare 平面文件 | `cell_lines` + `external_references(source='cellosaurus')` | 273 MPM 细胞系 / 83 xrefs |
| **DepMap 24Q4** | figshare 27993248(portal 被 Cloudflare 拦截) | `cell_lines`(38 打通)+ `vulnerabilities` + `alterations` + `external_references(source='depmap')` | 378 vulnerabilities + 472 xrefs |
| **ChEMBL** | `www.ebi.ac.uk/chembl/api/data/` | `drugs` + `external_references(source='chembl')` | 25 药物 / 11 靶点 / 25 mechanism / 25 xrefs |
| **OncoKB(公开层)** | `www.oncokb.org/api/v1/utils/cancerGeneList` + `/levels` | `external_references(source='oncokb')` | 9/18 seed 命中 / 9 xrefs |
| **CIViC(GraphQL)** | `civicdb.org/api/graphql` | `alterations` + `external_references(source='civic')` | 18/18 seed 命中 / 186 证据 |

**已明确不做**:文献 LLM 抽取 / PMC 全文 / pubmed_embedding / 向量数据库 / MESOMICS / dbGaP / COSMIC(license)/ 中国 CDE(无 API)。

### 3.3 后续 Phase 规划(骨架已留)

- **cases / specimens / molecular_profiles / variant_calls**:V2 §13 定义,当前表已建、行数为 0,下期填入 GDC clinical + cBioPortal patient-level 数据
- **文献抽取**:`ingest/extract.py` + `ingest/prompts/` + `ingest/moulds/` 已有骨架,下期启用 LiteratureSearch + LLM 结构化抽取
- **imaging_feature / pathology_feature**:`biomarker_type` 枚举已保留,下期填入影像组学 + 数字病理特征

---

## 4. 数据模型 (Schema)

### 4.1 全表清单(19 表 + 1 视图)

**Phase 1 核心 5 表**
- `biomarkers` — 20 行(18 gene-level + PDCD1 + ctDNA)
- `biomarker_clinical_uses` — 28 行,M2M,BEST 分类
- `studies` — 21 行
- `cohorts` — 21 行
- `evidence` — 67 行

**Phase 1 支撑 3 表**
- `external_references` — **877 行**,多源汇入的核心表
- `data_sources` — 5 行,provenance
- `extraction_runs` — 2 行,抽取批次

**Phase 2 新增 8 表**
- `genes` — 18 行,seed 基因元数据(entrez + uniprot + role + core_18_flag)
- `alterations` — 87 行,mutation / cna_del / cna_amp / fusion(按 gene+type+protein_change 去重)
- `cell_lines` — 273 行,cvcl_id + depmap_id + status 字段
- `drugs` — 25 行,ChEMBL 分子
- `clinical_trials` — 385 行,NCT id 为主键
- `interventions` — 793 行,试验臂 × 药物
- `vulnerabilities` — 378 行,DepMap Chronos essentiality
- `variant_calls` — 骨架(0 行)

**Phase 2 骨架 2 表(下期填数)**
- `cases` — 0 行
- `specimens` — 0 行
- `molecular_profiles` — 0 行

**汇总视图**
- `biomarker_multi_source_view` — 一行一 biomarker,列 = 每源 xref 计数 + 总 xref + 总 evidence

### 4.2 关键设计原则

**1. UPSERT 去重**
- `alterations` 键:(gene_entrez_id, alteration_type, protein_change) → 相同病变从多源来只存一行
- `cell_lines` 键:cvcl_id UNIQUE → Cellosaurus 与 DepMap 通过 RRID/CVCL 匹配后共享一行
- `clinical_trials` 键:nct_id 为主键

**2. 别名解析**
`_load_biomarker_map()` 会为每个 biomarker 索引所有 SEED_ANNOTATIONS 别名,DepMap 传 `EFEMP1` 时自动映射到数据库里的 canonical row `FBLN3`,同样处理 `GLUT1↔SLC2A1`、`PD-L1↔CD274`、`p16↔CDKN2A`。

**3. 多源合并保证**
每条源特定记录都写入 `external_references`,`biomarker_id` 指向唯一 canonical biomarker,`source` 字段区分来源,`payload` 字段(JSON)存储该源的原始细节。查询任意 biomarker 只需一次 GROUP BY 即可拉出全部源。

**4. CN 每-细胞系细节保留**
Copy-number loss 用 xref `external_id="CN:{ModelID}:{Symbol}"` 存 per-cell-line 精度,同时在 `alterations` 存 canonical `cna_del` 行(共享),互不冲突。

**5. SQLite / PostgreSQL 双兼容**
所有 ENUM 用 VARCHAR CHECK 替代,`database.py` 里对非 SQLite dialect 才启用 `pool_size` / `max_overflow`。日期字段用 ISO 字符串 + `_parse_date()` 兜底容错(处理 `YYYY-MM-DD` / `YYYY-MM` / `YYYY` 三种格式)。

---

## 5. 技术栈与目录结构

### 5.1 技术栈

| 层 | 选型 |
|---|---|
| 数据库(生产) | PostgreSQL 15+,启用 pg_trgm 全文检索 |
| 数据库(开发/交付) | SQLite(单文件 mpm_biomarker_db.sqlite,1.3 MB) |
| ORM | SQLAlchemy 2.0 |
| 迁移 | Alembic(三个版本:0001 initial / 0002 mould_fields / 0003 v2_expansion) |
| 后端 | FastAPI + Pydantic v2,自动 OpenAPI 文档 |
| 前端 | Next.js 14(App Router) + TypeScript + Tailwind CSS |
| 容器化 | Docker Compose(db + api + web) |

### 5.2 项目目录

```
mpm_biomarker_db/
├── README.md
├── docker-compose.yml
├── mpm_biomarker_db.sqlite            ← 交付 DB(1.3 MB)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/versions/
│   │   ├── 0001_initial.py            ← Phase 1 建表
│   │   ├── 0002_mould_fields.py       ← 文献抽取字段
│   │   └── 0003_v2_expansion.py       ← Phase 2 新增 9 表 + 视图 + 枚举扩容
│   └── app/
│       ├── main.py, config.py, database.py, types.py
│       ├── models/
│       │   ├── __init__.py            ← Phase 1 5 张核心表
│       │   ├── v2_models.py           ← Phase 2 8 张扩展表
│       │   └── enums.py
│       ├── schemas/                   ← Pydantic
│       └── routers/                   ← FastAPI 路由(biomarkers/evidence/studies)
├── frontend/                          ← Next.js 骨架
├── ingest/
│   ├── extract.py, pipeline.py, mapping.py    ← Phase 1 抽取脚手架
│   ├── prompts/, moulds/                       ← LLM 抽取模板(下期启用)
│   ├── fetchers/
│   │   ├── uniprot.py, opentargets.py, gdc.py, geo.py    ← Phase 1 fetcher
│   ├── v2_sources/                             ← Phase 2 新增
│   │   ├── ctgov.py, cellosaurus.py, depmap.py
│   │   ├── chembl.py, oncokb.py, civic.py
│   │   ├── mapping_v2.py                       ← 7 mapper + 编排器
│   │   └── v2_pipeline.py                      ← 端到端流水线
│   └── tests/
│       ├── test_mapping.py            ← 11 v1 测试
│       └── test_mapping_v2.py         ← 8 v2 测试(19/19 pass)
└── reports/
    ├── phase2_v2_ingest_report.md     ← Phase 2 数据 + 洞察
    └── project_specification.md       ← 本文件
```

### 5.3 缓存策略

每个 v2 fetcher 都是 cache-first:
- 缓存目录:`/mnt/shared-workspace/shared/<source>_mpm.json`(session 内 7 天有效)
- DepMap 大 CSV:`/workspace/depmap_cache/`(961 MB,单机本地)
- 删除缓存 → 重新抓取;保留缓存 → 冷启动流水线 ~10 min,热启动 ~1 s

---

## 6. API 接口

### 6.1 已实现(Phase 1)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/biomarkers` | 列表 + 过滤(clinical_use / biomarker_type / q) |
| GET | `/api/biomarkers/{id}` | 详情 + 嵌套 evidence |
| POST | `/api/biomarkers` | 创建 |
| GET | `/api/evidence` | 列表 + 过滤(biomarker / clinical_use / level / subtype) |
| POST | `/api/evidence` | 创建 |
| GET | `/api/studies` | 列表 |
| GET | `/api/studies/{id}` | 详情 + cohorts |
| GET | `/api/health` | 健康检查 |
| GET | `/docs` | Swagger UI |

### 6.2 待补(Phase 3 建议)

- `GET /api/biomarkers/{id}/multi-source` — 直接对接 `biomarker_multi_source_view`
- `GET /api/cell-lines` — 列表 + BAP1/NF2/CDKN2A/MTAP status 过滤
- `GET /api/drugs` — 药物列表 + target/modality/mpm_dev_stage 过滤
- `GET /api/trials` — 试验列表 + biomarker_eligibility 过滤
- `GET /api/vulnerabilities` — DepMap essentiality 查询
- `GET /api/alterations` — 突变/CNV 列表 + gene/type 过滤

---

## 7. 数据体量与关键指标

### 7.1 当前 DB 快照(mpm_biomarker_db.sqlite,1.3 MB)

| 类别 | 行数 |
|---|---:|
| biomarkers | 20 |
| genes | 18 |
| cell_lines | 273(38 有 DepMap ID) |
| drugs | 25 |
| clinical_trials | 385 |
| interventions | 793 |
| vulnerabilities | 378 |
| alterations | 87(62 mutation + 15 cna_del + 2 cna_amp + 8 unknown) |
| external_references | 877 |
| evidence | 67 |

### 7.2 多源覆盖 Top-10

| Symbol | ctgov | cellosaurus | depmap | chembl | oncokb | civic | total |
|---|---:|---:|---:|---:|---:|---:|---:|
| CDKN2A | 2 | 38 | 51 | 0 | 1 | 48 | **143** |
| EZH2 | 0 | 0 | 22 | 2 | 1 | 54 | **81** |
| CD274 | 11 | 0 | 22 | 13 | 1 | 28 | **78** |
| NF2 | 3 | 30 | 34 | 0 | 1 | 5 | **76** |
| BAP1 | 3 | 15 | 31 | 0 | 1 | 16 | **69** |
| MTAP | 2 | 0 | 45 | 0 | 1 | 3 | **53** |
| TERT | 0 | 0 | 21 | 2 | 1 | 17 | **43** |
| WT1 | 1 | 0 | 22 | 2 | 1 | 12 | **41** |
| MSLN | 12 | 0 | 21 | 5 | 0 | 0 | **40** |
| YAP1 | 0 | 0 | 23 | 0 | 1 | 3 | **29** |

### 7.3 生物学关键指标(可从 DB 直接查)

- **CDKN2A 纯合缺失**:32 个有 CN 数据的 MPM 系里 29 个(91%)+ 1 个杂合缺失(共 30/32 = 94% 有拷贝数丢失)
- **MTAP 共缺失**:19/32 纯合 + 5 杂合缺失 → 24/32 有拷贝数丢失(与 CDKN2A 9p21 tandem loss 一致)
- **YAP1 选择性依赖**:10 个 MPM 系 Chronos score < -0.5,其中 NCI-H226(-1.30)和 NCI-H2052(-1.29)是已发表 NF2-null Hippo 通路依赖模型 [1, 2]
- **CD274 药物 pipeline**:13 个 ChEMBL 分子(atezolizumab / durvalumab / avelumab / adebrelimab 等)
- **MSLN 靶向 pipeline**:5 个分子(amatuximab / anetumab ravtansine / LMB-100 / RG-7600 / SS1(dsFv)-PE38)+ 12 个 MSLN 相关 MPM 试验
- **CIViC MPM-tagged 证据**:7 条(BAP1 × 6 + NF2 × 1),其中 BAP1-olaparib 合成致死 Level B(SUBMITTED)是最高等级证据

---

## 8. 测试与验收

### 8.1 单元测试(19/19 pass)

**test_mapping.py**(v1,11 case):seed_data 插入 / 别名匹配 / evidence 分级 / clinical_use M2M / xref UPSERT / ...

**test_mapping_v2.py**(v2,8 case):
- `test_map_seed_genes` — 18 seed → genes 表建立
- `test_map_cellosaurus` — 273 MPM 系,CVCL UNIQUE,status 字段解析
- `test_map_depmap_vulnerabilities_and_alterations` — 9 vulnerabilities + 11 depmap xrefs(9 essentiality + 2 CN loss)+ hom_del / het_loss 分类
- `test_map_ctgov_trials_and_interventions` — 试验插入 + ISO 日期解析 + biomarker eligibility 挂载
- `test_map_chembl_targets_and_drugs` — target / mechanism / drug fan-out
- `test_map_oncokb_gene_annotations` — cancer gene list 命中
- `test_map_civic_evidence_items` — ACCEPTED + SUBMITTED 双状态入库 + MPM tagging
- `test_multi_source_grouping` — 同一 biomarker 从 6 源来的 xref GROUP BY 后 count 正确

### 8.2 SQL 验收(全部通过)

10 条验收查询(见 `reports/phase2_v2_ingest_report.md` §5),涵盖:
- 各表行数下限
- BAP1 从 6 源都能查到
- CDKN2A hom-del ≥ 28
- MSLN eligibility 试验 ≥ 12
- CIViC MPM-tagged ≥ 6

### 8.3 数据完整性约束

- `external_references.biomarker_id` 允许 NULL(有些细胞系/试验没关联到 seed biomarker)
- `alterations.protein_change` 允许 NULL(CN 缺失没有蛋白改变)
- `vulnerabilities.gene_entrez_id` + `cell_line_id` + `source` 组成 UNIQUE 约束
- `clinical_trials.nct_id` 主键 + `interventions.trial_nct_id` 外键

---

## 9. 假设与限制

### 9.1 明确假设

1. **BEST 分类**:采用 FDA-NIH 7 类框架,替代方案(3 类简化版)已弃
2. **证据分级**:A-F 6 级自定义 scale,替代方案(Oxford CEBM)已弃
3. **亚型强制分层**:每条 evidence 必带 subtype_scope,不折叠亚型效应
4. **UUID 内部主键**:外部引用通过独立表 external_references 保存,内部不用外部 ID
5. **CIViC 状态**:用户已确认 ACCEPTED + SUBMITTED 都入库,REJECTED 排除
6. **DepMap 版本**:24Q4(2024 Q4),记入 `data_sources.version`
7. **Cellosaurus MPM 匹配规则**:disease 字段包含 "esothelioma"(大小写不敏感),这会包括少数上呼吸道 / 腹膜间皮瘤系
8. **CN 阈值**:absolute CN < 0.5 = hom_del,0.5 ≤ CN < 1.5 = het_loss,CN ≥ 1.5 不记录(遵循 TCGA 惯例)
9. **OncoKB 免费层**:仅 cancerGeneList + levels,不含 token-gated `/annotate` 治疗证据

### 9.2 已知限制

1. **OncoKB 治疗证据缺失**:免费层无法拿到 per-variant 临床可用性等级
2. **CIViC SUBMITTED 未审核**:客户端可用 `WHERE json_extract(payload,'$.curation_status')='ACCEPTED'` 过滤到已审核部分
3. **CN 分类边界模糊**:接近 CN=0.5 的系会被划到 het_loss
4. **Cellosaurus 匹配范围**:MPM 匹配可能包含腹膜间皮瘤等非胸膜系(273 系里约 10-20 系可能不是纯胸膜来源)
5. **文献抽取尚未启动**:evidence 表只有 67 条手工 seed,未做 PubMed 系统抽取
6. **cases/specimens 骨架空**:受控数据(GDC clinical / cBioPortal patient-level)未接入
7. **不含影像/病理特征**:schema 已保留,数据下期填

---

## 10. 复现步骤

### 10.1 从 zero 复现 Phase 2 全量

```bash
# 1. 数据库准备(SQLite)
cd mpm_biomarker_db
cp /path/to/phase1/mpm_biomarker_db.sqlite /workspace/mpm_v2.db
DATABASE_URL="sqlite:////workspace/mpm_v2.db" PYTHONPATH=./backend \
  python3 -c "from app.database import Base, engine; \
              import app.models, app.models.v2_models; \
              Base.metadata.create_all(bind=engine, checkfirst=True)"

# 2. 抓取 6 源(缓存到 /mnt/shared-workspace/shared/*.json)
python3 -m ingest.v2_sources.ctgov       # ~5 min
python3 -m ingest.v2_sources.cellosaurus  # ~2 min
python3 -m ingest.v2_sources.depmap       # ~10 min(冷启动)
python3 -m ingest.v2_sources.chembl       # ~1 min
python3 -m ingest.v2_sources.oncokb       # ~30 s
python3 -m ingest.v2_sources.civic        # ~1 min

# 3. 编排映射
DATABASE_URL="sqlite:////workspace/mpm_v2.db" PYTHONPATH=./backend:. \
  python3 -m ingest.v2_sources.v2_pipeline --db sqlite:////workspace/mpm_v2.db

# 4. 单元测试
DATABASE_URL="sqlite:////workspace/test_v2.db" \
  PYTHONPATH=./backend:. python3 -m pytest -p no:cacheprovider \
  ingest/tests/test_mapping_v2.py -v

# 5. 交付
cp /workspace/mpm_v2.db mpm_biomarker_db.sqlite
```

### 10.2 Docker Compose 起本地栈

```bash
docker compose up --build
# → PostgreSQL 5432 / FastAPI 8000 (Swagger /docs) / Next.js 3000
```

---

## 11. 后续路线图

### Phase 3(建议)

1. **补 API**(§6.2):multi-source / cell-lines / drugs / trials / vulnerabilities / alterations 六路 REST endpoint
2. **前端多源仪表盘**:每个 biomarker 详情页展示 6 源 xref 分布(桑基图或雷达图)
3. **文献抽取启用**:`ingest/extract.py` + LiteratureSearch,批次入 evidence 表
4. **cases / specimens 填数**:通过 GDC clinical + cBioPortal patient-level API

### Phase 4(建议)

1. **液体活检模块**:ctDNA / miRNA / 血清蛋白面板(schema 已留)
2. **影像组学 / 数字病理**:CT 形态学 + 组织学亚型特征
3. **Neo4j 知识图谱**:biomarker-drug-trial-pathway 关联图
4. **图数据 + RAG**:向量检索 + LLM 回答"BAP1-loss MPM 患者可选的临床试验"这类跨源问题
5. **中国站点标注**:CDE / ChiCTR 与 CT.gov 合并,支持"含中国 site 的试验"过滤

---

## 12. 参考文献

[1] Yang H, et al. NF2 and canonical Hippo–YAP pathway define distinct tumor subsets characterized by different immune deficiency and treatment implications in human pleural mesothelioma. *Cancers* 2021. DOI: [10.3390/cancers13071561](https://doi.org/10.3390/cancers13071561)

[2] Calvet L, et al. YAP1 is essential for malignant mesothelioma tumor maintenance. *BMC Cancer* 2022. DOI: [10.1186/s12885-022-09686-y](https://doi.org/10.1186/s12885-022-09686-y)

---

**文件位置**
- 项目根:`mpm_biomarker_db/`
- 交付 DB:`mpm_biomarker_db/mpm_biomarker_db.sqlite`(1.3 MB)
- 数据报告:`mpm_biomarker_db/reports/phase2_v2_ingest_report.md`
- 本规范书:`mpm_biomarker_db/reports/project_specification.md`
