# MOSS GitHub商业化策略指南
**日期**: 2026-03-24  
**当前状态**: 完全开源 (MIT License)  
**目标**: 开源社区 + 商业变现平衡

---

## 当前GitHub状态分析

### 现有配置
| 项目 | 当前状态 | 商业化影响 |
|------|----------|------------|
| **License** | MIT | 允许商用，但无保护 |
| **代码公开** | 100%公开 | 竞争对手可完全复制 |
| **仓库** | public | 无法隐藏核心算法 |
| **Releases** | 开源版 | 无商业版区分 |
| **Issues** | 公开讨论 | 客户问题暴露 |

### 风险点
1. **无竞争壁垒** - 任何人可复制代码做竞品
2. **无法收费** - 代码完全免费，只能收服务费
3. **知识产权** - 无专利保护，开源即公开
4. **客户信任** - 企业客户可能担心代码公开安全性

---

## 商业化GitHub策略选项

### 方案A: 双许可模式 (推荐)
**开源核心 + 商业扩展**

```
GitHub结构:
├── moss/ (public) - 开源核心
│   ├── v3/ (9D基础系统)
│   └── v4-core/ (基础真实世界桥接)
├── moss-enterprise/ (private) - 商业扩展
│   ├── v4-enterprise/ (企业功能)
│   ├── security-hardened/ (强化安全)
│   └── saas-platform/ (SaaS平台)
└── moss-docs/ (public) - 文档
```

**GitHub操作**:
1. 创建私有仓库 `moss-enterprise`
2. 将商业功能移至私有仓库
3. 开源版保留基础功能，吸引社区
4. 商业版提供高级功能（多实例、企业安全、SaaS）

**License改变**:
- 开源版: **AGPL** (强制开源衍生作品) 或保持MIT
- 商业版: **Proprietary** (闭源收费)

**优点**:
- ✅ 保留社区影响力
- ✅ 有竞争壁垒
- ✅ 可收费订阅
- ✅ 企业客户安心

**缺点**:
- ⚠️ 需要维护两个代码库
- ⚠️ 社区可能反感"分裂"

---

### 方案B: 开放核心模式 (Open Core)
**所有代码公开，但功能分级**

```
GitHub结构:
moss/ (public)
├── v3/ - 完整开源 (个人/学术免费)
├── v4-core/ - 基础功能 (免费)
├── v4-enterprise/ - 企业功能 (需License Key)
└── v4-saas/ - SaaS平台 (按用量收费)
```

**实现方式**:
1. 代码中插入License验证
2. 企业功能需要激活码
3. SaaS版本自建平台，GitHub只放客户端

**GitHub操作**:
- 保持单仓库public
- 添加License验证模块
- 发布不同版本(binary releases)

**License改变**:
- **Server Side Public License (SSPL)** - MongoDB模式
- 或 **Elastic License** - 代码可见但商用需付费

**优点**:
- ✅ 单仓库维护简单
- ✅ 透明度高，客户信任
- ✅ 社区贡献仍可接受

**缺点**:
- ⚠️ 技术绕过风险高
- ⚠️ 法务复杂（License争议）

---

### 方案C: 完全闭源 (不推荐)
**转为私有仓库，仅发布binary**

**GitHub操作**:
1. 将moss转为private仓库
2. 或迁移至GitLab私有实例
3. GitHub仅保留marketing页面

**风险**:
- ❌ 失去社区支持
- ❌ 无法吸引贡献者
- ❌ 信任度降低

---

## 推荐实施方案 (方案A变体)

### 步骤1: 立即执行 (本周)

```bash
# 1. 创建企业版私有仓库
curl -H "Authorization: token $GITHUB_TOKEN" \
  -X POST https://api.github.com/user/repos \
  -d '{"name":"moss-enterprise","private":true}'

# 2. 复制核心代码到新仓库
git clone --bare https://github.com/luokaishi/moss.git
cd moss.git
git push --mirror https://github.com/luokaishi/moss-enterprise.git

# 3. 开源版保留基础功能
cd /workspace/projects/moss
# 删除/移动企业功能到私有仓库
```

### 步骤2: License更新

**开源版 (moss/public)**:
```
# LICENSE.txt
MOSS Community Edition
Copyright (c) 2026 Cash (luokaishi)

Licensed under the Apache License 2.0

You may use this software for personal and academic purposes.
Commercial use requires a separate Enterprise License.
```

**商业版 (moss-enterprise/private)**:
```
MOSS Enterprise Edition
Copyright (c) 2026 Cash (luokaishi)

This software is proprietary and confidential.
Unauthorized copying, distribution, or use is strictly prohibited.
Commercial licenses available at: https://moss-ai.com/pricing
```

### 步骤3: 功能分级

| 功能 | 社区版 (免费) | 企业版 (付费) |
|------|---------------|---------------|
| 9D基础系统 | ✅ | ✅ |
| Run 4.x实验 | ✅ | ✅ |
| 单机部署 | ✅ | ✅ |
| **多实例协作** | ❌ | ✅ |
| **企业安全审计** | ❌ | ✅ |
| **SaaS平台** | ❌ | ✅ |
| **SLA保障** | ❌ | ✅ |
| **专属支持** | ❌ | ✅ |

---

## GitHub具体改动清单

### 立即改动 (本周)
- [ ] 创建 `moss-enterprise` 私有仓库
- [ ] 更新开源版LICENSE (Apache 2.0 + 商业限制)
- [ ] README中添加商业版链接
- [ ] 创建 `SPONSORS.md` (GitHub Sponsors)

### 短期改动 (3月内)
- [ ] 分离企业功能代码
- [ ] 设置GitHub Actions (双仓库同步)
- [ ] 创建商业版landing page (GitHub Pages)
- [ ] 添加Pricing页面

### 长期改动 (6月内)
- [ ] GitHub Apps集成 (简化部署)
- [ ] Marketplace发布 (如有)
- [ ] 安全漏洞赏金计划
- [ ] 企业客户专用支持渠道

---

## 商业模式对照

| 模式 | GitHub改动 | 收入来源 |
|------|------------|----------|
| **开源+服务** | 最小改动 | 咨询/定制开发 |
| **双许可** | 私有仓库 | 订阅费/授权费 |
| **Open Core** | License验证 | 功能解锁费 |
| **SaaS** | 客户端开源 | 平台使用费 |

---

## 建议决策

**如果走商业化，推荐**:
1. **本周**: 创建私有仓库，分离核心算法
2. **本月**: 发布社区版v4.1.0，企业版内测
3. **下月**: 定价策略，接受预订
4. **6月**: v4.0正式商业发布

**是否执行GitHub商业化改动？**
